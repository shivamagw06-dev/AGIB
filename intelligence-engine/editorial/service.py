"""EditorialService — AGIB brain → structured JSON → rewrite-only editorial prose."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from editorial.cache import get_cache
from editorial.flags import is_enabled
from editorial.gemini_provider import GeminiProvider
from editorial.logging_util import log_editorial_event
from editorial.package import sanitize_structured
from editorial.prompts import EDITORIAL_SYSTEM, word_limit_for
from editorial.provider import EditorialProvider
from editorial.schema import EDITORIAL_VERSION, PROGRAMME
from editorial.template_fallback import render_template

_WORD_RE = re.compile(r"\s+")
_ADVICE_LINE = re.compile(
    r"(?im)^\s*(recommendation|action|rating|call|target\s*price)\s*:\s*.+$"
)
_ADVICE_VERBS = re.compile(
    r"\b(buy|sell|hold|accumulate|avoid|overweight|underweight)\b",
    re.I,
)
_IMPERATIVE = re.compile(
    r"\b(you should|investors should|we recommend|recommend buying|recommend selling|"
    r"target price|price target|take (profit|position)|enter|exit the stock)\b",
    re.I,
)


def _word_count(text: str) -> int:
    return len([w for w in _WORD_RE.split((text or "").strip()) if w])


def _clamp_words(text: str, max_words: int) -> str:
    words = [w for w in _WORD_RE.split((text or "").strip()) if w]
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:") + "."


def strip_advice_language(text: str) -> str:
    """Remove any advice / recommendation language Gemini may have emitted."""
    if not text:
        return ""
    lines = []
    for line in str(text).splitlines():
        if _ADVICE_LINE.search(line):
            continue
        if _IMPERATIVE.search(line):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    # Soften residual action verbs used as advice leads ("Buy this stock…") without
    # erasing factual quality labels that happen to contain those words elsewhere.
    cleaned = re.sub(
        r"(?i)\b(we|i)\s+(buy|sell|hold|accumulate|avoid)\b",
        "the package notes",
        cleaned,
    )
    cleaned = re.sub(
        r"(?i)^\s*(buy|sell|hold|accumulate|avoid)\b([\s,:—-]+)",
        "Observation: ",
        cleaned,
    )
    return cleaned.strip(" \n")


def compose_with_agib_recommendation(editorial_text: str, structured: dict[str, Any]) -> str:
    """AGIB owns the recommendation line; editorial supplies rewritten summary only."""
    reco = str(structured.get("recommendation") or "").strip()
    if not reco:
        return editorial_text
    conviction = str(structured.get("conviction") or "").strip()
    horizon = str(structured.get("investment_horizon") or "").strip()
    head = f"Recommendation: {reco}"
    if conviction:
        head += f" ({conviction})"
    body = strip_advice_language(editorial_text)
    parts = [head, "", body]
    if horizon and horizon.lower() not in body.lower():
        parts.append(f"Investment Horizon: {horizon}.")
    return "\n".join(p for p in parts if p is not None).strip()


def resolve_provider(name: str | None = None) -> EditorialProvider:
    """Factory for future OpenAI / Claude / Mistral / DeepSeek providers."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        provider_name = (name or settings.editorial_provider or "gemini").strip().lower()
        if provider_name in {"gemini", "google", "google_gemini"}:
            return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    except Exception:
        return GeminiProvider()


def _await_rewrite(provider: EditorialProvider, **kwargs: Any) -> dict[str, Any]:
    """Run provider.rewrite safely from sync Ask AGI paths."""
    coro = provider.rewrite(**kwargs)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result(timeout=45)


class EditorialService:
    """Editorial Intelligence Layer — rewrite only. AGIB remains the brain."""

    def __init__(self, provider: EditorialProvider | None = None) -> None:
        self.provider = provider or resolve_provider()
        self.cache = get_cache()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if is_enabled() else "disabled",
            "programme": PROGRAMME,
            "version": EDITORIAL_VERSION,
            "role": "writer_only",
            "agib_is_brain": True,
            "gemini_is_writer_only": True,
            "never_generates_advice": True,
            "never_recommends_actions": True,
            "provider": self.provider.health(),
            "cache_ttl_hours": 24,
            "word_limits": {
                "quick_summary": 60,
                "quick_analysis": 120,
                "detailed_analysis": 400,
            },
        }

    def _run(
        self,
        *,
        mode: str,
        structured: dict[str, Any],
        question: str | None = None,
        max_words: int | None = None,
        use_cache: bool = True,
        attach_agib_recommendation: bool = False,
    ) -> dict[str, Any]:
        clean = sanitize_structured(structured)
        clean["mode"] = mode
        if question:
            clean["question"] = question
        limit = max_words or word_limit_for(mode)

        cache_key = self.cache.make_key(mode, clean, question)
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                log_editorial_event(
                    event="editorial_cache_hit",
                    question=question,
                    structured=clean,
                    response=cached.get("text"),
                    provider=cached.get("provider"),
                    mode=mode,
                    cache_hit=True,
                    latency_ms=0,
                    token_usage=cached.get("usage"),
                )
                return {**cached, "cache_hit": True, "fallback": False}

        text = None
        meta: dict[str, Any] = {}
        error = None
        try:
            if is_enabled():
                result = _await_rewrite(
                    self.provider,
                    mode=mode,
                    structured=clean,
                    question=question,
                    max_words=limit,
                )
                text = strip_advice_language(str(result.get("text") or ""))
                text = _clamp_words(text, limit)
                meta = {
                    "provider": result.get("provider") or self.provider.name,
                    "model": result.get("model"),
                    "usage": result.get("usage") or {},
                    "latency_ms": result.get("latency_ms"),
                    "prompt": result.get("prompt"),
                }
        except Exception as exc:  # noqa: BLE001 — must never fail the request
            error = str(exc)
            log_editorial_event(
                event="editorial_provider_failed",
                question=question,
                structured=clean,
                error=error,
                provider=getattr(self.provider, "name", None),
                mode=mode,
            )

        fallback = False
        if not text:
            text = render_template(mode, clean)
            text = strip_advice_language(text)
            text = _clamp_words(text, limit)
            fallback = True
            meta = {
                "provider": "template_fallback",
                "model": None,
                "usage": {},
                "latency_ms": 0,
                "prompt": None,
            }
            log_editorial_event(
                event="editorial_template_fallback",
                question=question,
                structured=clean,
                response=text,
                provider="template_fallback",
                mode=mode,
                error=error,
            )

        rewritten = text
        display = (
            compose_with_agib_recommendation(rewritten, clean)
            if attach_agib_recommendation
            else rewritten
        )

        out = {
            "enabled": True,
            "programme": PROGRAMME,
            "version": EDITORIAL_VERSION,
            "role": "writer_only",
            "mode": mode,
            "text": display,
            "rewritten_summary": rewritten,
            "word_count": _word_count(rewritten),
            "max_words": limit,
            "structured_intelligence": clean,
            "recommendation_from_agib_only": True,
            "never_invented_facts": True,
            "never_generates_advice": True,
            "editorial_system": EDITORIAL_SYSTEM[:180],
            "fallback": fallback,
            "cache_hit": False,
            "error": error,
            **meta,
        }
        if use_cache and not fallback:
            self.cache.set(cache_key, out)
        return out

    def generateQuickSummary(
        self,
        structured: dict[str, Any],
        *,
        question: str | None = None,
        attach_agib_recommendation: bool = False,
    ) -> dict[str, Any]:
        return self._run(
            mode="quick_summary",
            structured=structured,
            question=question,
            max_words=60,
            use_cache=True,
            attach_agib_recommendation=attach_agib_recommendation,
        )

    def generateRecommendation(
        self,
        structured: dict[str, Any],
        *,
        question: str | None = None,
    ) -> dict[str, Any]:
        """Legacy name — editorial still only rewrites; AGIB recommendation may be attached."""
        return self.generateQuickSummary(
            structured,
            question=question,
            attach_agib_recommendation=True,
        )

    def generateQuickAnalysis(
        self,
        structured: dict[str, Any],
        *,
        question: str | None = None,
    ) -> dict[str, Any]:
        return self._run(
            mode="quick_analysis",
            structured=structured,
            question=question,
            max_words=120,
            use_cache=True,
            attach_agib_recommendation=False,
        )

    def generateDetailedAnalysis(
        self,
        structured: dict[str, Any],
        *,
        question: str | None = None,
    ) -> dict[str, Any]:
        return self._run(
            mode="detailed_analysis",
            structured=structured,
            question=question,
            max_words=400,
            use_cache=False,
            attach_agib_recommendation=False,
        )


def generateQuickSummary(
    structured: dict[str, Any],
    *,
    question: str | None = None,
) -> dict[str, Any]:
    return EditorialService().generateQuickSummary(structured, question=question)


def generateRecommendation(
    structured: dict[str, Any],
    *,
    question: str | None = None,
) -> dict[str, Any]:
    return EditorialService().generateRecommendation(structured, question=question)


def generateQuickAnalysis(
    structured: dict[str, Any],
    *,
    question: str | None = None,
) -> dict[str, Any]:
    return EditorialService().generateQuickAnalysis(structured, question=question)


def generateDetailedAnalysis(
    structured: dict[str, Any],
    *,
    question: str | None = None,
) -> dict[str, Any]:
    return EditorialService().generateDetailedAnalysis(structured, question=question)

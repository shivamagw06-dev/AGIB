"""EditorialService — AGIB brain → structured JSON → editorial writer → final answer."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from editorial.cache import get_cache
from editorial.flags import is_enabled
from editorial.gemini_provider import GeminiProvider
from editorial.logging_util import log_editorial_event
from editorial.package import sanitize_structured
from editorial.provider import EditorialProvider
from editorial.schema import EDITORIAL_VERSION, PROGRAMME
from editorial.template_fallback import render_template

_WORD_RE = re.compile(r"\s+")


def _word_count(text: str) -> int:
    return len([w for w in _WORD_RE.split((text or "").strip()) if w])


def _clamp_words(text: str, max_words: int) -> str:
    words = [w for w in _WORD_RE.split((text or "").strip()) if w]
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:") + "."


def _preserve_recommendation(text: str, structured: dict[str, Any]) -> str:
    """Ensure Gemini did not override AGIB's recommendation."""
    reco = str(structured.get("recommendation") or "").strip()
    if not reco:
        return text
    # If response already leads with the recommendation, keep it.
    if re.search(rf"recommendation\s*:\s*{re.escape(reco)}", text or "", re.I):
        return text
    conviction = str(structured.get("conviction") or "").strip()
    head = f"Recommendation: {reco}"
    if conviction:
        head += f" ({conviction})"
    body = (text or "").strip()
    # Strip any alternate recommendation lead Gemini may have invented.
    body = re.sub(r"(?i)^recommendation\s*:\s*[^\n]+", "", body).strip()
    return f"{head}\n\n{body}".strip()


def resolve_provider(name: str | None = None) -> EditorialProvider:
    """Factory for future OpenAI / Claude / Mistral / DeepSeek providers."""
    provider_name = (name or "gemini").strip().lower()
    try:
        from app.core.config import get_settings

        settings = get_settings()
        provider_name = (name or settings.editorial_provider or "gemini").strip().lower()
        if provider_name in {"gemini", "google", "google_gemini"}:
            return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        # Future providers soft-map to Gemini until implemented — never crash.
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

    # Already inside an event loop — run in a worker thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result(timeout=45)


class EditorialService:
    """Editorial Intelligence Layer entrypoint.

    AGIB supplies structured intelligence. Providers only write prose.
    """

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
            "provider": self.provider.health(),
            "cache_ttl_hours": 24,
        }

    def _run(
        self,
        *,
        mode: str,
        structured: dict[str, Any],
        question: str | None = None,
        max_words: int = 60,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        clean = sanitize_structured(structured)
        clean["mode"] = mode
        if question:
            clean["question"] = question

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
                    max_words=max_words,
                )
                text = _preserve_recommendation(str(result.get("text") or ""), clean)
                text = _clamp_words(text, max_words)
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
            text = _clamp_words(text, max_words)
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

        out = {
            "enabled": True,
            "programme": PROGRAMME,
            "version": EDITORIAL_VERSION,
            "role": "writer_only",
            "mode": mode,
            "text": text,
            "word_count": _word_count(text),
            "max_words": max_words,
            "structured_intelligence": clean,
            "recommendation_preserved": True,
            "never_invented_facts": True,
            "fallback": fallback,
            "cache_hit": False,
            "error": error,
            **meta,
        }
        if use_cache and not fallback:
            self.cache.set(cache_key, out)
        return out

    def generateRecommendation(
        self,
        structured: dict[str, Any],
        *,
        question: str | None = None,
    ) -> dict[str, Any]:
        return self._run(
            mode="recommendation",
            structured=structured,
            question=question,
            max_words=60,
            use_cache=True,
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
            max_words=60,
            use_cache=True,
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
            max_words=180,
            use_cache=False,
        )


# Public function API requested by the architecture brief.
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

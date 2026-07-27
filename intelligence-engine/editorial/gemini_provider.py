"""Gemini editorial provider — writer only. Never analyses documents or markets."""

from __future__ import annotations

import time
from typing import Any

from editorial.logging_util import log_editorial_event
from editorial.prompts import build_prompt
from editorial.provider import EditorialProvider


class GeminiProvider(EditorialProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or "gemini-2.0-flash").strip() or "gemini-2.0-flash"

    def health(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "role": "writer_only",
            "available": bool(self.api_key),
            "model": self.model,
            "never_analyses": True,
            "never_overrides_recommendation": True,
        }

    async def rewrite(
        self,
        *,
        mode: str,
        structured: dict[str, Any],
        question: str | None = None,
        max_words: int = 60,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        import httpx

        prompt = build_prompt(mode=mode, structured=structured, question=question, max_words=max_words)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json={
                    "systemInstruction": {
                        "parts": [
                            {
                                "text": (
                                    "You are AGIB's Editorial Intelligence Layer. "
                                    "You rewrite structured AGIB intelligence into institutional prose. "
                                    "You do not analyse markets, filings, or valuations. "
                                    "You never change the recommendation."
                                )
                            }
                        ]
                    },
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2},
                },
            )
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        if not response.is_success:
            detail = response.text[:300]
            log_editorial_event(
                event="gemini_http_error",
                question=question,
                structured=structured,
                prompt=prompt,
                latency_ms=latency_ms,
                error=f"{response.status_code}: {detail}",
                provider=self.name,
                mode=mode,
            )
            raise RuntimeError(f"Gemini editorial failed ({response.status_code})")

        payload = response.json()
        parts = (((payload.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        text = "".join(str(part.get("text") or "") for part in parts).strip()
        usage = payload.get("usageMetadata") or {}
        token_usage = {
            "prompt_tokens": usage.get("promptTokenCount"),
            "candidates_tokens": usage.get("candidatesTokenCount"),
            "total_tokens": usage.get("totalTokenCount"),
        }
        log_editorial_event(
            event="gemini_rewrite_ok",
            question=question,
            structured=structured,
            prompt=prompt,
            response=text,
            latency_ms=latency_ms,
            token_usage=token_usage,
            provider=self.name,
            mode=mode,
        )
        if not text:
            raise RuntimeError("Gemini returned empty editorial text")
        return {
            "text": text,
            "model": self.model,
            "provider": self.name,
            "usage": token_usage,
            "latency_ms": latency_ms,
            "prompt": prompt,
        }

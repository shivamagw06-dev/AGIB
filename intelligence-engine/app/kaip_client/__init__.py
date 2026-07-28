"""Thin Intelligence Engine client for KAIP published knowledge (read-only)."""

from app.kaip_client.client import KaipClient, KaipClientError

__all__ = ["KaipClient", "KaipClientError"]

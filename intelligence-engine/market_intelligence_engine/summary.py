"""AGI market summary — interpretation, not recommendation."""

from __future__ import annotations

from typing import Any


def market_summary(
    overview: dict[str, Any],
    sectors: list[dict[str, Any]],
    breadth: dict[str, Any],
    flows: dict[str, Any],
) -> str:
    parts: list[str] = []

    avg_pe = (overview.get("averages") or {}).get("pe")
    if avg_pe is not None:
        parts.append(f"The covered universe trades at a median P/E of {avg_pe:.1f}x.")

    attractive = [s for s in sectors if s.get("opportunity") == "Attractive"]
    premium = [s for s in sectors if s.get("opportunity") == "Premium"]
    if attractive:
        parts.append(
            f"{', '.join(s['sector'] for s in attractive[:3])} "
            f"{' sits' if len(attractive) == 1 else ' sit'} below typical historical valuation bands."
        )
    if premium:
        parts.append(
            f"{premium[0]['sector']} continues to trade at a premium versus its own history."
        )

    if breadth.get("ok"):
        parts.append(
            f"Market breadth is {breadth.get('heatmap', 'mixed').lower()} "
            f"({breadth.get('advancing', 0)} advancing vs {breadth.get('declining', 0)} declining)."
        )

    if flows.get("available") and flows.get("explanation"):
        parts.append(flows["explanation"])

    if not parts:
        return (
            "Market summary will populate once warehouse valuation and flow coverage are complete. "
            "No buy or sell view is implied."
        )
    parts.append("This is institutional context, not investment advice.")
    return " ".join(parts)

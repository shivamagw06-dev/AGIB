from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.registry import register_agent
from app.schemas.models import (
    AgentOutput,
    ConfidenceBreakdown,
    DebatePackage,
    DeskType,
    EvidenceItem,
    Finding,
    InstitutionalReport,
    ScenarioCase,
    SourceType,
)


@register_agent
class ChiefInvestmentOfficer(BaseAgent):
    """
    CIO synthesizes only. It does not orchestrate agents.
    Research Director supplies the evidence package + debate.
    """

    agent_id = "cio"
    mission = "Weigh competing analyst views and produce the final institutional investment thesis."

    async def analyze(self, context: dict[str, Any]) -> AgentOutput:
        # CIO also exposes synthesize() used by the Director; analyze() kept for registry completeness.
        report = await self.synthesize(context)
        evidence = report.supporting_evidence[:1] or [
            EvidenceItem(
                claim="CIO synthesis completed",
                source_id="internal:cio",
                source_type=SourceType.INTERNAL,
                reliability=0.6,
            )
        ]
        return AgentOutput(
            agent_id=self.agent_id,
            mission=self.mission,
            findings=[
                Finding(
                    statement=report.executive_summary[:400],
                    evidence_ids=[evidence[0].evidence_id],
                    confidence=report.confidence.score,
                )
            ],
            evidence=evidence if isinstance(evidence, list) else [evidence],
            confidence=report.confidence,
            assumptions=["Analyst evidence package is complete enough for synthesis"],
            invalidators=["Material new evidence that reverses the debate balance"],
        )

    async def synthesize(self, context: dict[str, Any]) -> InstitutionalReport:
        outputs: list[AgentOutput] = context.get("agent_outputs") or []
        debate: DebatePackage | None = context.get("debate")
        confidence: ConfidenceBreakdown = context.get("confidence") or ConfidenceBreakdown(
            score=50,
            supports=[],
            challenges=["Missing confidence package"],
            rationale="Default confidence because no combined score was provided.",
        )
        evidence: list[EvidenceItem] = context.get("evidence") or []
        desk = context.get("desk") or DeskType.SMOKE

        key_findings = []
        for output in outputs:
            for finding in output.findings[:2]:
                key_findings.append(finding.statement)

        bull_points = next((p.points for p in (debate.positions if debate else []) if p.side == "bull"), [])
        bear_points = next((p.points for p in (debate.positions if debate else []) if p.side == "bear"), [])
        base_points = next((p.points for p in (debate.positions if debate else []) if p.side == "base"), [])

        thesis = (
            f"AGI CIO synthesizes a {confidence.score}% confidence institutional view because "
            f"{len(outputs)} analyst packages and {len(evidence)} evidence items were provided. "
        )
        if debate and debate.unresolved_conflicts:
            thesis += "Unresolved conflicts remain and are treated as scenario risk rather than settled facts. "
        if key_findings:
            thesis += f"Lead finding: {key_findings[0]}"

        # Optional OpenAI enrichment — fails soft to deterministic synthesis
        enriched = await self._maybe_enrich(thesis, key_findings, debate, confidence)
        executive = enriched or thesis

        return InstitutionalReport(
            desk=desk if isinstance(desk, DeskType) else DeskType(str(desk)),
            title="AGI Institutional Research Note",
            executive_summary=executive,
            key_findings=key_findings[:8],
            macro_view=next((o.findings[0].statement for o in outputs if o.agent_id == "macro_economist" and o.findings), None),
            market_view=next((o.findings[0].statement for o in outputs if o.agent_id == "market_analyst" and o.findings), None),
            sector_view=None,
            company_view=None,
            technical_view=None,
            valuation_view=None,
            catalysts=[p for p in base_points[:4]],
            risks=[p for p in bear_points[:4]] + [c for c in confidence.challenges[:3]],
            bull_case=ScenarioCase(
                label="Bull",
                probability=max(10, min(40, 100 - confidence.score)),
                detail="; ".join(bull_points[:3]) or "Upside requires confirmation from breadth and macro transmission.",
                is_prediction=True,
            ),
            base_case=ScenarioCase(
                label="Base",
                probability=confidence.score,
                detail="; ".join(base_points[:3]) or executive[:240],
                is_prediction=True,
            ),
            bear_case=ScenarioCase(
                label="Bear",
                probability=max(10, min(40, 100 - confidence.score)),
                detail="; ".join(bear_points[:3]) or "Downside if invalidators in the evidence package trigger.",
                is_prediction=True,
            ),
            confidence=confidence,
            supporting_evidence=evidence[:20],
            action_items=[
                "Monitor evidence invalidators listed by analysts",
                "Re-run desk if AGIB cache freshness deteriorates",
                "Treat scenario cases as probabilities, not forecasts of fact",
            ],
        )

    async def _maybe_enrich(
        self,
        thesis: str,
        findings: list[str],
        debate: DebatePackage | None,
        confidence: ConfidenceBreakdown,
    ) -> str | None:
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.openai_api_key:
            return None
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are AGI's Chief Investment Officer. Synthesize a 180-260 word institutional thesis. "
                            "Cite reasoning with because-what. Never invent data. Mark scenarios as scenarios. "
                            "No buy/sell recommendations."
                        ),
                    },
                    {
                        "role": "user",
                        "content": str(
                            {
                                "draft": thesis,
                                "findings": findings,
                                "debate": debate.model_dump() if debate else None,
                                "confidence": confidence.model_dump(),
                            }
                        ),
                    },
                ],
            )
            text = response.choices[0].message.content
            return text.strip() if text else None
        except Exception:
            return None

"""KUL knowledge providers — thin wrappers over existing engines. No new knowledge."""

from __future__ import annotations

from knowledge_unification.providers.academy import AcademyProvider
from knowledge_unification.providers.capiq_ikt import CapIqIktProvider
from knowledge_unification.providers.cgl import ContinuousGatherProvider
from knowledge_unification.providers.company_memory import CompanyMemoryProvider
from knowledge_unification.providers.financial_concepts import FinancialConceptsProvider
from knowledge_unification.providers.financial_foundations import FinancialFoundationsProvider
from knowledge_unification.providers.financial_statement_intelligence import (
    FinancialStatementIntelligenceProvider,
)
from knowledge_unification.providers.ikl import IklProvider
from knowledge_unification.providers.knowledge_factory import KnowledgeFactoryProvider
from knowledge_unification.providers.legacy_kip import LegacyKipProvider

ALL_PROVIDERS = (
    CapIqIktProvider,
    IklProvider,
    CompanyMemoryProvider,
    KnowledgeFactoryProvider,
    ContinuousGatherProvider,
    FinancialConceptsProvider,
    FinancialFoundationsProvider,
    FinancialStatementIntelligenceProvider,
    AcademyProvider,
    LegacyKipProvider,
)

__all__ = ["ALL_PROVIDERS"]

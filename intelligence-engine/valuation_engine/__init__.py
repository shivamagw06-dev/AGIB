"""Unified Valuation Engine — one valuation, read by every AGI product.

Warehouse in, valuation out:

    Upstox / Yahoo / Capital IQ -> DQIV -> Warehouse -> engine -> consumers

The engine never calls a vendor. Swapping a provider changes what the warehouse
holds, not how a multiple is computed.
"""

from valuation_engine.service import (
    ENGINE_CODE,
    VERSION,
    explain_valuation_change,
    get_company_valuation,
    get_sector_valuation,
    health,
)
from valuation_engine import terminal
from valuation_engine.prompt import (
    OUTPUT_SECTIONS,
    UVE_INSTITUTIONAL_SYSTEM_PROMPT_V3,
    UVE_PROMPT_VERSION,
    is_valuation_question,
    prompt_catalog,
    system_prompt as uve_system_prompt,
)

__all__ = [
    "ENGINE_CODE",
    "VERSION",
    "OUTPUT_SECTIONS",
    "UVE_INSTITUTIONAL_SYSTEM_PROMPT_V3",
    "UVE_PROMPT_VERSION",
    "explain_valuation_change",
    "get_company_valuation",
    "get_sector_valuation",
    "health",
    "is_valuation_question",
    "prompt_catalog",
    "terminal",
    "uve_system_prompt",
]

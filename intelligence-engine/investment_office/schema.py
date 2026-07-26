"""Investment Office schema constants."""

from __future__ import annotations

IO_VERSION = "investment-office-v1.0.0"
PROGRAMME = "AGI_INVESTMENT_OFFICE"
PROGRAMME_SHORT = "Investment Office"

PRIORITY = ("Critical", "High", "Medium", "Low")

ATTENTION_REASONS = (
    "Results Released",
    "Guidance Changed",
    "Margins Compressed",
    "Valuation Expanded",
    "Debt Increased",
    "Credit Rating Changed",
    "Management Change",
    "Research Outdated",
    "Prediction Failed",
    "Knowledge Coverage Low",
    "House View Review Suggested",
    "Material Monitor Change",
)

COPILOT_PROMPTS = (
    "What deserves my attention today?",
    "Which companies changed materially overnight?",
    "Which sectors improved?",
    "What research should I publish today?",
    "Which predictions are failing?",
    "What knowledge did AGI learn in the last 24 hours?",
)

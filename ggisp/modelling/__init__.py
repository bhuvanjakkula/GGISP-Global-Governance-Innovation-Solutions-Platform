"""Quantitative policy models for sovereign debt, development finance, and cross-domain simulation."""
from ggisp.modelling.cross_domain import CrossDomainAssumptions, simulate_cross_domain
from ggisp.modelling.development_finance import (
    DevelopmentFinanceAssumptions,
    simulate_development_allocation,
)
from ggisp.modelling.sovereign_debt import (
    DynamicDebtAssumptions,
    simulate_debt,
)

# For backward compatibility with starter v0.1 tests and callers:
DebtAssumptions = DynamicDebtAssumptions
simulate = simulate_debt

__all__ = [
    "DynamicDebtAssumptions",
    "DebtAssumptions",
    "simulate_debt",
    "simulate",
    "DevelopmentFinanceAssumptions",
    "simulate_development_allocation",
    "CrossDomainAssumptions",
    "simulate_cross_domain",
]

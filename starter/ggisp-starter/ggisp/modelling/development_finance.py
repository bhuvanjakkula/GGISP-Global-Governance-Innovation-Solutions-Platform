"""Development Finance Allocation Engine.

Optimizes concessional financing allocation across human development,
infrastructure, and climate adaptation while monitoring debt sustainability.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class DevelopmentFinanceAssumptions(BaseModel):
    total_financing_pool_million_usd: float = Field(ge=1.0, le=100000.0, default=2500.0)
    country_gdp_million_usd: float = Field(ge=100.0, le=30000000.0, default=110000.0)
    annual_govt_revenue_million_usd: float = Field(ge=10.0, le=10000000.0, default=19000.0)
    current_annual_debt_service_million_usd: float = Field(ge=0.0, le=5000000.0, default=4800.0)
    
    # Priority weighting sliders (0 to 100)
    infrastructure_weight: float = Field(ge=0.0, le=100.0, default=35.0)
    healthcare_weight: float = Field(ge=0.0, le=100.0, default=25.0)
    education_weight: float = Field(ge=0.0, le=100.0, default=20.0)
    climate_adaptation_weight: float = Field(ge=0.0, le=100.0, default=20.0)
    
    # Concessional loan terms
    concessional_interest_rate_percent: float = Field(ge=0.0, le=15.0, default=1.8)
    grant_element_share_percent: float = Field(ge=0.0, le=100.0, default=30.0)
    loan_maturity_years: int = Field(ge=5, le=50, default=25)


SECTOR_MULTIPLIERS = {
    "infrastructure": {"gdp_multiplier": 1.45, "sdg_focus": ["SDG 9: Industry & Infra", "SDG 7: Clean Energy"]},
    "healthcare": {"gdp_multiplier": 1.25, "sdg_focus": ["SDG 3: Good Health & Well-being", "SDG 1: No Poverty"]},
    "education": {"gdp_multiplier": 1.35, "sdg_focus": ["SDG 4: Quality Education", "SDG 8: Decent Work"]},
    "climate_adaptation": {"gdp_multiplier": 1.18, "sdg_focus": ["SDG 13: Climate Action", "SDG 14/15: Ecosystems"]},
}


def simulate_development_allocation(a: DevelopmentFinanceAssumptions) -> Dict[str, Any]:
    """Calculate sector capital distribution, economic impact multipliers, and debt absorption."""
    total_weight = (
        a.infrastructure_weight
        + a.healthcare_weight
        + a.education_weight
        + a.climate_adaptation_weight
    )
    if total_weight <= 0:
        total_weight = 100.0

    # Sector shares
    shares = {
        "infrastructure": a.infrastructure_weight / total_weight,
        "healthcare": a.healthcare_weight / total_weight,
        "education": a.education_weight / total_weight,
        "climate_adaptation": a.climate_adaptation_weight / total_weight,
    }

    pool = a.total_financing_pool_million_usd
    allocations = {}
    weighted_multiplier = 0.0

    for sector, share in shares.items():
        amount = pool * share
        mult = SECTOR_MULTIPLIERS[sector]["gdp_multiplier"]
        weighted_multiplier += share * mult
        allocations[sector] = {
            "allocated_million_usd": round(amount, 2),
            "share_percent": round(share * 100, 1),
            "direct_gdp_multiplier": mult,
            "estimated_long_term_gdp_impact_usd": round(amount * mult, 2),
            "sdg_alignment": SECTOR_MULTIPLIERS[sector]["sdg_focus"],
        }

    # Grant vs Loan breakdown
    grant_amount = pool * (a.grant_element_share_percent / 100.0)
    loan_amount = pool - grant_amount
    annual_amortization = loan_amount / a.loan_maturity_years if a.loan_maturity_years > 0 else 0.0
    annual_interest = loan_amount * (a.concessional_interest_rate_percent / 100.0)
    new_annual_debt_service = annual_amortization + annual_interest

    total_projected_debt_service = a.current_annual_debt_service_million_usd + new_annual_debt_service
    debt_service_to_revenue_ratio = (
        (total_projected_debt_service / a.annual_govt_revenue_million_usd) * 100.0
        if a.annual_govt_revenue_million_usd > 0
        else 0.0
    )

    # Sustainability status (IMF/World Bank benchmark: >18-20% is elevated risk for developing sovereigns)
    if debt_service_to_revenue_ratio > 25.0:
        sustainability_rating = "Critical Risk — Debt service severely impairs essential domestic expenditures"
    elif debt_service_to_revenue_ratio > 18.0:
        sustainability_rating = "Elevated Risk — High absorption of tax revenue for debt service"
    else:
        sustainability_rating = "Sustainable — Concessional debt service absorbs manageable share of revenue"

    composite_sdg_score = round(min(weighted_multiplier * 55.0, 100.0), 1)

    return {
        "total_financing_pool_million_usd": pool,
        "grant_amount_million_usd": round(grant_amount, 2),
        "concessional_loan_amount_million_usd": round(loan_amount, 2),
        "sector_allocations": allocations,
        "composite_weighted_multiplier": round(weighted_multiplier, 3),
        "composite_sdg_impact_score_100": composite_sdg_score,
        "projected_annual_concessional_debt_service_million_usd": round(new_annual_debt_service, 2),
        "total_annual_debt_service_million_usd": round(total_projected_debt_service, 2),
        "debt_service_to_revenue_percent": round(debt_service_to_revenue_ratio, 2),
        "sustainability_rating": sustainability_rating,
        "methodology": "Concessional multi-sector portfolio allocation using empirical MDB multiplier weights and revenue absorption constraints.",
    }

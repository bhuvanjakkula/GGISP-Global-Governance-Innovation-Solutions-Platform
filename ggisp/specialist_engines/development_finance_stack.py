"""Specialist Engine 12: Blended Finance Capital Stack & MDB Mobilization Multiplier.
Reference: OECD Blended Finance Principles / DFI Working Group on Blended Concessional Finance.
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class BlendedFinanceInput(BaseModel):
    project_total_capex_million_usd: float = Field(default=500.0, ge=10.0, le=50000.0)
    concessional_first_loss_grant_million_usd: float = Field(default=50.0, ge=1.0, le=5000.0, description="De-risking anchor capital")
    multilateral_subordinated_loan_million_usd: float = Field(default=150.0, ge=0.0, le=20000.0, description="MDB concessional tranche")
    target_commercial_senior_debt_million_usd: float = Field(default=300.0, ge=0.0, le=30000.0, description="Private institutional debt")
    project_projected_economic_irr_percent: float = Field(default=14.5, ge=1.0, le=50.0)
    sovereign_credit_spread_bps: float = Field(default=450.0, ge=50.0, le=2500.0)


def simulate_blended_finance(inp: BlendedFinanceInput) -> Dict[str, Any]:
    """Calculate private capital mobilization ratio (PCM), blended cost of capital, and de-risking multiplier."""
    total_capital = (
        inp.concessional_first_loss_grant_million_usd
        + inp.multilateral_subordinated_loan_million_usd
        + inp.target_commercial_senior_debt_million_usd
    )

    # Private capital mobilization leverage ratio: Private Commercial / Public Concessional
    public_de_risking_capital = inp.concessional_first_loss_grant_million_usd + inp.multilateral_subordinated_loan_million_usd
    private_mobilization_ratio = inp.target_commercial_senior_debt_million_usd / public_de_risking_capital if public_de_risking_capital > 0 else 0.0

    # Weighted Average Cost of Capital (WACC):
    # Grant cost = 0%, MDB sub loan = 2.5%, Senior private debt = SOFR (5.0%) + Spread (4.5%) = 9.5%
    w_grant = inp.concessional_first_loss_grant_million_usd / total_capital if total_capital > 0 else 0
    w_mdb = inp.multilateral_subordinated_loan_million_usd / total_capital if total_capital > 0 else 0
    w_private = inp.target_commercial_senior_debt_million_usd / total_capital if total_capital > 0 else 0

    cost_grant = 0.0
    cost_mdb = 2.5
    cost_private = 5.0 + (inp.sovereign_credit_spread_bps / 100.0)
    blended_wacc = (w_grant * cost_grant) + (w_mdb * cost_mdb) + (w_private * cost_private)

    # Net Economic Margin: Economic IRR - Blended WACC
    economic_margin = inp.project_projected_economic_irr_percent - blended_wacc

    return {
        "engine": "Blended Finance Capital Stack & MDB Mobilization Engine",
        "domain": "development-finance",
        "project_total_capex_million_usd": inp.project_total_capex_million_usd,
        "private_capital_mobilization_ratio": f"1 : {round(private_mobilization_ratio, 2)}",
        "blended_weighted_average_cost_of_capital_percent": round(blended_wacc, 2),
        "unblended_commercial_borrowing_cost_percent": round(cost_private, 2),
        "interest_cost_savings_spread_percent": round(cost_private - blended_wacc, 2),
        "net_economic_spread_margin_percent": round(economic_margin, 2),
        "bankability_assessment": (
            "HIGHLY BANKABLE & COMMERCIALLY VIABLE: Subordinated first-loss tranche compresses borrowing cost below economic rate of return."
            if economic_margin > 3.0
            else "MARGINAL BANKABILITY: Requires additional concessional grant de-risking to attract private institutional capital."
        ),
        "framework_reference": "G20 Principles for Quality Infrastructure Investment & DFI Enhanced Blended Finance Guidelines.",
    }

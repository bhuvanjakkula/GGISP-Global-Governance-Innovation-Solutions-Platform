"""Specialist Engine 11: OECD Pillar Two GloBE 15% Global Minimum Tax Simulator.
Reference: OECD/G20 Inclusive Framework on BEPS / Global Anti-Base Erosion (GloBE) Rules.
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class InternationalTaxInput(BaseModel):
    jurisdiction_code: str = Field(default="KEN", min_length=2, max_length=5)
    in_scope_mne_global_revenue_euro_million: float = Field(default=850.0, ge=750.0, description="In-scope threshold is >= 750M EUR")
    local_constituent_entity_profit_million_usd: float = Field(default=120.0, ge=1.0, le=50000.0)
    covered_taxes_paid_million_usd: float = Field(default=10.8, ge=0.0, le=20000.0)
    substance_based_income_exclusion_payroll_percent: float = Field(default=9.6, ge=5.0, le=10.0, description="Payroll carve-out %")
    local_payroll_cost_million_usd: float = Field(default=18.0, ge=0.0, le=5000.0)
    tangible_assets_million_usd: float = Field(default=35.0, ge=0.0, le=10000.0)
    substance_based_income_exclusion_assets_percent: float = Field(default=7.6, ge=5.0, le=8.0, description="Tangible assets carve-out %")
    global_minimum_tax_rate_percent: float = Field(default=15.0)


def simulate_international_tax(inp: InternationalTaxInput) -> Dict[str, Any]:
    """Calculate Effective Tax Rate (ETR), Substance-Based Carve-outs, and Top-Up Tax under OECD Pillar Two."""
    profit = inp.local_constituent_entity_profit_million_usd
    covered_taxes = inp.covered_taxes_paid_million_usd

    # Effective Tax Rate: ETR = Covered Taxes / GloBE Income
    etr = (covered_taxes / profit) * 100.0 if profit > 0 else 0.0

    # Top-up tax percentage: Top-up % = max(15% - ETR, 0%)
    top_up_percentage = max(inp.global_minimum_tax_rate_percent - etr, 0.0)

    # Substance-based income exclusion (SBIE):
    payroll_carveout = inp.local_payroll_cost_million_usd * (inp.substance_based_income_exclusion_payroll_percent / 100.0)
    assets_carveout = inp.tangible_assets_million_usd * (inp.substance_based_income_exclusion_assets_percent / 100.0)
    total_sbie = payroll_carveout + assets_carveout

    # Excess profit subject to top-up tax:
    excess_profit = max(profit - total_sbie, 0.0)
    jurisdictional_top_up_tax_million = excess_profit * (top_up_percentage / 100.0)

    return {
        "engine": "OECD Pillar Two GloBE Global Minimum Tax Simulator",
        "domain": "international-tax",
        "jurisdiction": inp.jurisdiction_code,
        "effective_tax_rate_etr_percent": round(etr, 2),
        "statutory_minimum_tax_threshold_percent": inp.global_minimum_tax_rate_percent,
        "top_up_tax_rate_gap_percent": round(top_up_percentage, 2),
        "substance_based_income_exclusion_million_usd": round(total_sbie, 2),
        "excess_profit_taxable_base_million_usd": round(excess_profit, 2),
        "projected_top_up_tax_revenue_million_usd": round(jurisdictional_top_up_tax_million, 2),
        "pillar_two_compliance_status": (
            "TAX HAVEN / LOW-TAX EXPOSURE: Top-up tax applies via Qualified Domestic Minimum Top-up Tax (QDMTT) or Income Inclusion Rule (IIR)."
            if top_up_percentage > 0.0
            else "COMPLIANT JURISDICTION: ETR meets or exceeds the 15% international minimum standard."
        ),
        "international_architecture": "OECD/G20 Base Erosion and Profit Shifting (BEPS) 2.0 Two-Pillar Solution.",
    }

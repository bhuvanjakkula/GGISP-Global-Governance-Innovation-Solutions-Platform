"""Specialist Engine 10: High Seas Marine Biodiversity & BBNJ Fishery Harvest Model.
Reference: UN BBNJ Treaty (High Seas Treaty) / UNCLOS Article 118 / FAO Code of Conduct for Responsible Fisheries.
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class OceanGovernanceInput(BaseModel):
    carrying_capacity_k_thousand_tons: float = Field(default=2500.0, ge=100.0, le=100000.0)
    current_biomass_thousand_tons: float = Field(default=1100.0, ge=10.0, le=100000.0)
    intrinsic_growth_rate_r: float = Field(default=0.35, ge=0.05, le=1.5)
    authorized_catch_thousand_tons: float = Field(default=180.0, ge=0.0, le=20000.0)
    iuu_illegal_fishing_factor_percent: float = Field(default=25.0, ge=0.0, le=100.0)
    marine_protected_area_coverage_percent: float = Field(default=12.0, ge=0.0, le=50.0, description="30x30 Protected High Seas Area %")


def simulate_ocean_governance(inp: OceanGovernanceInput) -> Dict[str, Any]:
    """Calculate Schaefer production curve, Maximum Sustainable Yield (MSY), and BBNJ 30x30 conservation gains."""
    k = inp.carrying_capacity_k_thousand_tons
    r = inp.intrinsic_growth_rate_r
    b = inp.current_biomass_thousand_tons

    # Maximum Sustainable Yield: MSY = (r * K) / 4 at B_msy = K / 2
    msy = (r * k) / 4.0
    b_msy = k / 2.0

    # Total catch including IUU (Illegal, Unreported, Unregulated) fishing:
    total_effective_catch = inp.authorized_catch_thousand_tons * (1.0 + inp.iuu_illegal_fishing_factor_percent / 100.0)

    # Surplus production Schaefer equation: dB/dt = r * B * (1 - B/K) - Catch
    natural_surplus_production = r * b * (1.0 - (b / k))
    net_biomass_change = natural_surplus_production - total_effective_catch

    # MPA 30x30 spillover boost (replenishment multiplier):
    mpa_benefit = (inp.marine_protected_area_coverage_percent / 100.0) * (0.25 * natural_surplus_production)
    adjusted_net_change = net_biomass_change + mpa_benefit

    # Depletion status
    biomass_ratio_to_msy = b / b_msy
    if biomass_ratio_to_msy < 0.5:
        stock_status = "CRITICALLY DEPLETED / COLLAPSED — Mandatory moratorium on commercial extraction"
    elif biomass_ratio_to_msy < 1.0:
        stock_status = "OVERFISHED — Below B_msy; harvest reductions required under BBNJ Treaty"
    else:
        stock_status = "SUSTAINABLE HARVEST — Biomass above Maximum Sustainable Yield threshold"

    return {
        "engine": "High Seas Marine Biodiversity & BBNJ Harvest Engine",
        "domain": "ocean-governance",
        "maximum_sustainable_yield_msy_kt": round(msy, 2),
        "biomass_msy_target_kt": round(b_msy, 2),
        "current_biomass_ratio_to_bmsy": round(biomass_ratio_to_msy, 2),
        "total_harvest_including_iuu_kt": round(total_effective_catch, 2),
        "iuu_illegal_harvest_estimate_kt": round(total_effective_catch - inp.authorized_catch_thousand_tons, 2),
        "projected_annual_biomass_trajectory_kt": round(adjusted_net_change, 2),
        "mpa_conservation_spillover_gain_kt": round(mpa_benefit, 2),
        "bbnj_treaty_conservation_status": stock_status,
        "treaty_reference": "UN Agreement on Marine Biological Diversity of Areas Beyond National Jurisdiction (BBNJ / High Seas Treaty 2023).",
    }

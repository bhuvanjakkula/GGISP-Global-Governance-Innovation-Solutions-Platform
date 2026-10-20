"""Specialist Engine 9: Critical Minerals Supply Chain Concentration & Circularity Model.
Reference: IEA Critical Minerals Market Review / US Geological Survey (USGS) Mineral Commodity Summaries.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CriticalMineralsInput(BaseModel):
    mineral_type: str = Field(default="lithium", description="Mineral: lithium, cobalt, nickel, rare_earths, copper")
    top_country_market_share_percent: float = Field(default=68.0, ge=10.0, le=99.0, description="Share of global refining in top nation (e.g. China)")
    second_country_market_share_percent: float = Field(default=16.0, ge=1.0, le=50.0)
    third_country_market_share_percent: float = Field(default=8.0, ge=1.0, le=30.0)
    annual_global_demand_kt: float = Field(default=165.0, ge=1.0, le=50000.0, description="Kilotonnes per year")
    circular_recycling_recovery_percent: float = Field(default=12.0, ge=0.0, le=80.0, description="Closed-loop scrap recycling recovery rate %")
    geopolitical_embargo_shock_percent: float = Field(default=25.0, ge=0.0, le=100.0, description="Hypothetical export restriction shock %")


def simulate_critical_minerals(inp: CriticalMineralsInput) -> Dict[str, Any]:
    """Calculate Herfindahl-Hirschman Index (HHI), supply vulnerability, and recycling offsets."""
    s1 = inp.top_country_market_share_percent
    s2 = inp.second_country_market_share_percent
    s3 = inp.third_country_market_share_percent
    remainder = max(100.0 - (s1 + s2 + s3), 0.0)
    # Assume remainder split among 4 smaller producers
    s_other = remainder / 4.0

    # Herfindahl-Hirschman Index (0 to 10,000):
    # HHI > 2500 is classified as Highly Concentrated by antitrust and trade authorities
    hhi = (s1 ** 2) + (s2 ** 2) + (s3 ** 2) + 4 * (s_other ** 2)

    # Net supply available under geopolitical embargo shock:
    gross_disruption_kt = inp.annual_global_demand_kt * (inp.geopolitical_embargo_shock_percent / 100.0) * (s1 / 100.0)
    circular_recycled_kt = inp.annual_global_demand_kt * (inp.circular_recycling_recovery_percent / 100.0)
    net_supply_deficit_kt = max(gross_disruption_kt - circular_recycled_kt, 0.0)
    deficit_share_percent = (net_supply_deficit_kt / inp.annual_global_demand_kt) * 100.0 if inp.annual_global_demand_kt > 0 else 0.0

    return {
        "engine": "Critical Minerals Supply Chain Concentration & Circularity Engine",
        "domain": "critical-minerals",
        "mineral_type": inp.mineral_type.upper(),
        "herfindahl_hirschman_index_hhi": round(hhi, 1),
        "market_concentration_tier": "Highly Concentrated (HHI > 2500)" if hhi > 2500 else ("Moderately Concentrated" if hhi > 1500 else "Diversified"),
        "annual_recycled_material_offset_kt": round(circular_recycled_kt, 1),
        "potential_net_supply_deficit_kt": round(net_supply_deficit_kt, 1),
        "net_supply_deficit_share_percent": round(deficit_share_percent, 1),
        "strategic_recommendation": (
            "CRITICAL CHOKEPOINT RISK: Establish strategic reserve buffer stocks, bilateral off-take diversification, and domestic battery hydrometallurgical recycling mandates."
            if hhi > 2500
            else "MODERATE CONCENTRATION: Continue multilateral supplier partnerships and traceability compliance."
        ),
        "multilateral_reference": "IEA Critical Minerals Security Architecture & Minerals Security Partnership (MSP) Framework.",
    }

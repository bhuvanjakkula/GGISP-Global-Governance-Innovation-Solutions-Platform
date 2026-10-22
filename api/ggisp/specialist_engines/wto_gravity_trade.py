"""Specialist Engine 3: Structural Gravity Trade Model & Maritime Chokepoint Risk Index.
Reference: WTO Economic Research / Tinbergen-Anderson Structural Gravity Equation.
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class GravityTradeInput(BaseModel):
    exporter_gdp_billion_usd: float = Field(default=115.0, ge=1.0, le=30000.0, description="Exporter GDP in billion USD")
    importer_gdp_billion_usd: float = Field(default=18000.0, ge=1.0, le=30000.0, description="Importer GDP in billion USD")
    distance_km: float = Field(default=6800.0, ge=100.0, le=25000.0, description="Geodesic bilateral distance in km")
    has_free_trade_agreement: bool = Field(default=True, description="Bilateral or regional trade agreement in force")
    common_language: bool = Field(default=True)
    applied_tariff_percent: float = Field(default=8.5, ge=0.0, le=100.0, description="Average applied bilateral tariff rate %")
    chokepoint_exposure: str = Field(default="suez_and_bab_el_mandeb", description="Transit chokepoints: none, malacca, suez_and_bab_el_mandeb, panama, hormuz")


CHOKEPOINT_RISK_FACTORS = {
    "none": 0.0,
    "malacca": 0.12,
    "suez_and_bab_el_mandeb": 0.28,
    "panama": 0.15,
    "hormuz": 0.22,
}


def simulate_gravity_trade(inp: GravityTradeInput) -> Dict[str, Any]:
    """Calculate predicted trade volume using Anderson-van Wincoop gravity coefficients and chokepoint risks."""
    # Classical gravity equation: Trade = A * (GDP_exp^0.85 * GDP_imp^0.80) / (Dist^0.9) * exp(FTA * 0.45) * (1 + tariff)^(-1.5)
    gdp_exp = inp.exporter_gdp_billion_usd
    gdp_imp = inp.importer_gdp_billion_usd
    dist = inp.distance_km

    constant_a = 0.00015
    fta_mult = math.exp(0.45) if inp.has_free_trade_agreement else 1.0
    lang_mult = math.exp(0.25) if inp.common_language else 1.0
    tariff_factor = (1.0 + inp.applied_tariff_percent / 100.0) ** (-1.5)

    base_trade_billion = constant_a * (gdp_exp ** 0.85) * (gdp_imp ** 0.80) / (dist ** 0.90)
    modeled_trade_billion = base_trade_billion * fta_mult * lang_mult * tariff_factor

    # Chokepoint vulnerability deduction:
    choke_rate = CHOKEPOINT_RISK_FACTORS.get(inp.chokepoint_exposure, 0.0)
    freight_cost_surge_percent = choke_rate * 85.0
    adjusted_trade_billion = modeled_trade_billion * (1.0 - choke_rate * 0.40)
    trade_value_at_risk_million = (modeled_trade_billion - adjusted_trade_billion) * 1000.0

    return {
        "engine": "Structural Gravity Trade & Supply Chain Chokepoint Engine",
        "domain": "wto-trade",
        "predicted_bilateral_trade_volume_billion_usd": round(modeled_trade_billion, 3),
        "post_chokepoint_trade_volume_billion_usd": round(adjusted_trade_billion, 3),
        "annual_trade_value_at_risk_million_usd": round(trade_value_at_risk_million, 1),
        "freight_cost_premium_surge_percent": round(freight_cost_surge_percent, 1),
        "chokepoint_vulnerability_index_100": round(choke_rate * 100.0, 1),
        "free_trade_agreement_trade_creation_bonus_percent": round((fta_mult - 1.0) * 100.0, 1),
        "methodology": "Anderson & van Wincoop Structural Gravity Formulation (2003) with maritime chokepoint transit disruption elasticities.",
    }

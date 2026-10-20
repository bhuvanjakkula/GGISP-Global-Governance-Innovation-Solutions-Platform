"""Specialist Engine 13: Loss and Damage Parametric Disaster Trigger & Article 6 Carbon Engine.
Reference: UNFCCC COP28 Loss & Damage Fund / Paris Agreement Article 6 Rules / CCRIF SPC Architecture.
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class ClimateParametricInput(BaseModel):
    hazard_type: str = Field(default="tropical_cyclone_windspeed", description="Hazard: tropical_cyclone_windspeed, drought_rainfall_deficit, coastal_flood_surge")
    maximum_parametric_coverage_million_usd: float = Field(default=120.0, ge=5.0, le=2000.0)
    parametric_trigger_threshold_knots: float = Field(default=95.0, ge=64.0, le=160.0, description="Windspeed trigger in knots (Category 3+)")
    catastrophe_exhaustion_threshold_knots: float = Field(default=135.0, ge=100.0, le=200.0, description="Full 100% payout windspeed")
    recorded_event_intensity_knots: float = Field(default=115.0, ge=50.0, le=220.0, description="Satellite certified event windspeed")
    article_6_itmo_credits_tonnes_co2e: float = Field(default=2500000.0, ge=1000.0, le=100000000.0, description="High-integrity mitigation credits")
    carbon_credit_price_per_tonne_usd: float = Field(default=35.0, ge=5.0, le=250.0)
    days_to_guaranteed_payout: int = Field(default=5, ge=1, le=14, description="Parametric liquidity release window")


def simulate_climate_parametric(inp: ClimateParametricInput) -> Dict[str, Any]:
    """Calculate parametric emergency liquidity payout and Article 6 sovereign carbon revenue."""
    t_start = inp.parametric_trigger_threshold_knots
    t_max = inp.catastrophe_exhaustion_threshold_knots
    actual = inp.recorded_event_intensity_knots

    # Linear parametric payout scaling between trigger and exhaustion:
    if actual < t_start:
        payout_ratio = 0.0
    elif actual >= t_max:
        payout_ratio = 1.0
    else:
        payout_ratio = (actual - t_start) / (t_max - t_start)

    emergency_payout_million = inp.maximum_parametric_coverage_million_usd * payout_ratio

    # Article 6.2/6.4 ITMO carbon revenue generation:
    carbon_revenue_gross_million = (inp.article_6_itmo_credits_tonnes_co2e * inp.carbon_credit_price_per_tonne_usd) / 1e6
    # 5% share of proceeds adaptation deduction under Article 6.4:
    sop_adaptation_fund_deduction_million = carbon_revenue_gross_million * 0.05
    net_sovereign_carbon_revenue_million = carbon_revenue_gross_million - sop_adaptation_fund_deduction_million

    # Combined climate fiscal liquidity:
    total_immediate_liquidity_million = emergency_payout_million + net_sovereign_carbon_revenue_million

    return {
        "engine": "Loss and Damage Parametric Disaster Trigger & Article 6 Carbon Engine",
        "domain": "climate-finance",
        "hazard_type": inp.hazard_type,
        "parametric_trigger_breached": actual >= t_start,
        "payout_intensity_fraction_percent": round(payout_ratio * 100.0, 1),
        "emergency_disaster_liquidity_payout_million_usd": round(emergency_payout_million, 2),
        "payout_timeline_days": inp.days_to_guaranteed_payout,
        "article_6_carbon_revenue_net_million_usd": round(net_sovereign_carbon_revenue_million, 2),
        "total_available_climate_fiscal_headroom_million_usd": round(total_immediate_liquidity_million, 2),
        "fund_activation_status": (
            f"PARAMETRIC DISASTER TRIGGER ACTIVATED: Emergency disbursement of ${round(emergency_payout_million, 1)}M released within {inp.days_to_guaranteed_payout} days."
            if emergency_payout_million > 0
            else "BELOW PARAMETRIC THRESHOLD: No catastrophic emergency release triggered."
        ),
        "treaty_reference": "UNFCCC COP28 Operationalization of the Loss & Damage Fund & Paris Agreement Article 6.2/6.4 Cooperative Approaches.",
    }

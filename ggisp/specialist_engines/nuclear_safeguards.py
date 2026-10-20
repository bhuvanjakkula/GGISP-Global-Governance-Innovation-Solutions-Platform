"""Specialist Engine 1: Nuclear Safeguards, Material Accountancy & Breakout Time Model.
Reference: IAEA Safeguards Technical Reports / NPT Verification Architecture.
"""
from __future__ import annotations

import math
from typing import Any, Dict
from pydantic import BaseModel, Field


class NuclearSafeguardsInput(BaseModel):
    feed_enrichment_percent: float = Field(default=0.711, ge=0.2, le=5.0, description="Natural or LEU feed assay %")
    product_enrichment_percent: float = Field(default=60.0, ge=3.5, le=95.0, description="Current enriched product assay %")
    target_weapons_grade_percent: float = Field(default=90.0, ge=85.0, le=95.0, description="Weapons-grade threshold assay %")
    tails_assay_percent: float = Field(default=0.3, ge=0.1, le=0.5, description="Depleted tails assay %")
    cascade_separative_work_capacity_swu_yr: float = Field(default=15000.0, ge=100.0, le=500000.0, description="Total centrifuge capacity in SWU/year")
    current_stockpile_kg: float = Field(default=140.0, ge=0.0, le=5000.0, description="Current stock of product assay uranium (kg UF6)")
    critical_significant_quantity_kg: float = Field(default=25.0, ge=15.0, le=35.0, description="IAEA Significant Quantity for HEU (kg)")


def compute_separative_work(x: float) -> float:
    """Value function V(x) = (2x - 1) * ln(x / (1 - x)) where x is fractional assay."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return (2.0 * x - 1.0) * math.log(x / (1.0 - x))


def simulate_nuclear_safeguards(inp: NuclearSafeguardsInput) -> Dict[str, Any]:
    """Calculate Separative Work Units (SWU), required feed mass, and estimated breakout timeline."""
    xp = inp.target_weapons_grade_percent / 100.0
    xf = inp.product_enrichment_percent / 100.0
    xw = inp.tails_assay_percent / 100.0
    sq = inp.critical_significant_quantity_kg

    # Mass balance for 1 Significant Quantity of Weapons Grade Uranium:
    # F = P * (xp - xw) / (xf - xw)
    # W = F - P
    feed_factor = (xp - xw) / (xf - xw) if (xf - xw) > 0 else 1.0
    feed_required_kg = sq * feed_factor

    # SWU requirement per SQ:
    # SWU = P*V(xp) + W*V(xw) - F*V(xf)
    w_kg = feed_required_kg - sq
    v_xp = compute_separative_work(xp)
    v_xf = compute_separative_work(xf)
    v_xw = compute_separative_work(xw)
    swu_needed = sq * v_xp + w_kg * v_xw - feed_required_kg * v_xf
    swu_needed = max(swu_needed, 1.0)

    # Breakout time in days:
    annual_swu = inp.cascade_separative_work_capacity_swu_yr
    breakout_days = (swu_needed / annual_swu) * 365.25 if annual_swu > 0 else 999.0
    stockpile_sq_potential = inp.current_stockpile_kg / feed_required_kg if feed_required_kg > 0 else 0.0

    # IAEA Safeguards Inspection Frequency Rating:
    if breakout_days < 30.0:
        safeguards_tier = "Critical — Demands continuous online enrichment monitoring (OLEM) & daily physical inspection"
    elif breakout_days < 90.0:
        safeguards_tier = "High Alert — Weekly unannounced inspections & short-notice seal checks required"
    else:
        safeguards_tier = "Standard Verification — Monthly routine inspection & remote containment monitoring"

    return {
        "engine": "Nuclear Safeguards & Breakout Estimator",
        "domain": "nuclear-security",
        "swu_required_per_significant_quantity": round(swu_needed, 2),
        "feed_uranium_required_kg": round(feed_required_kg, 2),
        "estimated_breakout_time_days": round(breakout_days, 1),
        "stockpile_equivalent_sq_count": round(stockpile_sq_potential, 2),
        "safeguards_verification_protocol": safeguards_tier,
        "methodology": "Standard isotope separation cascade theory and IAEA Significant Quantity thresholds (IAEA Safeguards Manual).",
    }

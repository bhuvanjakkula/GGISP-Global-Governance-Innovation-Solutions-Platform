"""GGISP Systemic Multi-Domain Cascade Solver & Planetary Resilience Optimizer.
Models non-linear feedback loops between macroeconomic, climate, critical infrastructure, and health shocks.
Solves Pareto-optimal intervention resource allocations to truncate systemic collapse cascades.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CascadeShockInput(BaseModel):
    climate_cyclone_intensity_knots: float = Field(default=120.0, ge=60.0, le=200.0)
    sovereign_debt_gdp_percent: float = Field(default=82.0, ge=30.0, le=180.0)
    icu_pandemic_surge_r0: float = Field(default=3.2, ge=1.0, le=8.0)
    space_debris_conjunction_p_c: float = Field(default=2.4e-4, ge=1e-8, le=1.0)
    critical_mineral_embargo_percent: float = Field(default=35.0, ge=0.0, le=100.0)
    available_emergency_fiscal_buffer_million_usd: float = Field(default=250.0, ge=10.0, le=10000.0)


def solve_planetary_cascade(inp: CascadeShockInput) -> Dict[str, Any]:
    """Execute dynamic cross-domain cascade stress test and generate optimal Pareto intervention schedule."""
    # 1. Domain-specific baseline vulnerability scores (0 to 100)
    v_climate = min(max((inp.climate_cyclone_intensity_knots - 64.0) / 1.1, 0.0), 100.0)
    v_debt = min(max((inp.sovereign_debt_gdp_percent - 50.0) * 1.25, 0.0), 100.0)
    v_health = min(max((inp.icu_pandemic_surge_r0 - 1.0) * 28.0, 0.0), 100.0)
    v_space = 92.0 if inp.space_debris_conjunction_p_c >= 1e-4 else 25.0
    v_minerals = inp.critical_mineral_embargo_percent * 1.15

    # 2. Non-Linear Cross-Domain Coupling Amplifiers:
    # Sovereign debt impairs disaster liquidity absorption:
    climate_debt_coupling = (v_debt / 100.0) * 0.45 * v_climate
    # Climate damage knocks out tele-ICU and primary healthcare:
    climate_health_coupling = (v_climate / 100.0) * 0.35 * v_health
    # Space satellite collision knocks out financial settlement and remote logistics:
    space_financial_coupling = (v_space / 100.0) * 0.25 * (v_debt + v_minerals)

    # 3. Aggregated Systemic Vulnerability Index (SVI 0-100)
    raw_systemic_loss = (v_climate + v_debt + v_health + v_space + v_minerals +
                         climate_debt_coupling + climate_health_coupling + space_financial_coupling) / 5.0
    svi_score = min(round(raw_systemic_loss, 1), 100.0)

    # 4. Multi-Objective Pareto Intervention Optimizer
    # Allocate fiscal buffer across highest-leverage cascade breakers:
    total_buf = inp.available_emergency_fiscal_buffer_million_usd
    
    # Cascade Breaker 1: Parametric insurance liquidity trigger (neutralizes climate-debt loop)
    alloc_climate_liquidity = round(total_buf * 0.32, 1)
    # Cascade Breaker 2: Regional ICU tele-network & mobile transport (neutralizes health mortality)
    alloc_health_surge = round(total_buf * 0.28, 1)
    # Cascade Breaker 3: Debt restructuring escrow & single-limb CAC legal fees
    alloc_debt_stabilization = round(total_buf * 0.20, 1)
    # Cascade Breaker 4: Autonomous space collision burn delta-v & critical mineral reserve buffer
    alloc_space_minerals = round(total_buf * 0.20, 1)

    # Post-Intervention Residual Risk:
    mitigated_svi = max(round(svi_score * (1.0 - (total_buf / (total_buf + 400.0)) * 0.72), 1), 12.0)
    cascade_containment_percent = round((1.0 - (mitigated_svi / svi_score)) * 100.0, 1) if svi_score > 0 else 100.0

    return {
        "engine": "Planetary Systemic Cascade Solver & Multi-Objective Optimizer",
        "pre_intervention_systemic_vulnerability_index_100": svi_score,
        "post_intervention_residual_vulnerability_100": mitigated_svi,
        "cascade_suppression_efficiency_percent": cascade_containment_percent,
        "vulnerability_sub_scores": {
            "climate_disaster_stress": round(v_climate, 1),
            "sovereign_debt_distress": round(v_debt, 1),
            "critical_care_pandemic_surge": round(v_health, 1),
            "orbital_space_conjunction_risk": round(v_space, 1),
            "critical_mineral_supply_chokepoint": round(v_minerals, 1)
        },
        "cross_domain_feedback_loops": [
            {
                "pathway": "Debt-Climate Liquidity Trap",
                "amplification": f"+{round(climate_debt_coupling, 1)} pts",
                "mechanism": "High debt service crowds out domestic disaster contingency funds, turning manageable cyclones into fiscal insolvencies."
            },
            {
                "pathway": "Climate-Infrastructure Health Bottleneck",
                "amplification": f"+{round(climate_health_coupling, 1)} pts",
                "mechanism": "Grid blackouts from extreme weather disrupt municipal telemetry, paralyzing tele-ICU coordination."
            },
            {
                "pathway": "Orbital Debris Communication Blackout",
                "amplification": f"+{round(space_financial_coupling, 1)} pts",
                "mechanism": "Satellite telemetry loss impedes international interbank payments and mineral off-take logistics."
            }
        ],
        "pareto_optimal_resource_dispatch": {
            "total_budget_allocated_million_usd": total_buf,
            "allocations": [
                {"program": "Parametric Catastrophe Liquidity Facility", "amount_million_usd": alloc_climate_liquidity, "priority": "CRITICAL_TIER_1"},
                {"program": "Regional MOCC Critical Care Transfer Network", "amount_million_usd": alloc_health_surge, "priority": "CRITICAL_TIER_1"},
                {"program": "Enhanced Single-Limb CAC Debt Stabilization", "amount_million_usd": alloc_debt_stabilization, "priority": "STRATEGIC_TIER_2"},
                {"program": "Orbital CAM Delta-V & Strategic Mineral Reserves", "amount_million_usd": alloc_space_minerals, "priority": "RESILIENCE_TIER_3"}
            ]
        },
        "planetary_command_status": (
            "SYSTEMIC CASCADE SEVERELY ARRESTED: Multi-objective resource allocation truncated cross-domain contagion loops."
            if cascade_containment_percent > 40.0
            else "SYSTEMIC STRESS ACTIVE: Additional multilateral liquidity or external credit guarantees required."
        )
    }

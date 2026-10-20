"""Specialist Engine 7: Epidemiological SEIR Early-Warning & Vaccine Surge Allocator.
Reference: WHO International Health Regulations (IHR) / CEPI 100-Day Mission.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class GlobalHealthInput(BaseModel):
    total_population: float = Field(default=55000000.0, ge=10000.0, le=2000000000.0)
    initial_infected: int = Field(default=150, ge=1, le=100000)
    reproduction_number_r0: float = Field(default=2.8, ge=0.5, le=15.0)
    variant_immune_evasion_percent: float = Field(default=25.0, ge=0.0, le=100.0)
    days_to_diagnostic_sequencing: int = Field(default=7, ge=1, le=90)
    available_vaccine_doses_million: float = Field(default=12.0, ge=0.0, le=500.0)
    daily_administration_capacity: int = Field(default=80000, ge=1000, le=2000000)
    simulation_days: int = Field(default=90, ge=30, le=365)


def simulate_global_health(inp: GlobalHealthInput) -> Dict[str, Any]:
    """Run discrete SEIR epidemic projection with genomic immune evasion and vaccine surge."""
    # Effective R: R_eff = R_0 * (1 + immune_evasion/100)
    r_eff = inp.reproduction_number_r0 * (1.0 + inp.variant_immune_evasion_percent / 100.0)
    gamma = 1.0 / 7.0  # 7-day infectious period
    beta = r_eff * gamma
    sigma = 1.0 / 4.0  # 4-day incubation/latent period

    n = inp.total_population
    s = n - inp.initial_infected
    e = inp.initial_infected * 1.5
    i = float(inp.initial_infected)
    r = 0.0

    peak_infections = i
    peak_day = 0

    # Simulate discrete timeline
    for day in range(1, inp.simulation_days + 1):
        # Vaccination begins after sequencing confirmation
        vacc_rate = inp.daily_administration_capacity if day > inp.days_to_diagnostic_sequencing else 0
        new_inf = (beta * s * i) / n
        new_lat = sigma * e
        new_rec = gamma * i

        s = max(s - new_inf - vacc_rate, 0.0)
        e = max(e + new_inf - new_lat, 0.0)
        i = max(i + new_lat - new_rec, 0.0)
        r = r + new_rec + vacc_rate

        if i > peak_infections:
            peak_infections = i
            peak_day = day

    # ICU hospitalization stress (estimated 3.5% of active infected cases need critical care)
    icu_peak_need = round(peak_infections * 0.035)
    vaccine_coverage_achieved_percent = round((inp.available_vaccine_doses_million * 1e6 / n) * 100.0, 1)

    return {
        "engine": "Epidemiological SEIR Early-Warning & Surge Allocator",
        "domain": "global-health",
        "effective_reproduction_number_r_eff": round(r_eff, 2),
        "peak_active_infections_projected": round(peak_infections),
        "peak_epidemic_day": peak_day,
        "estimated_critical_care_icu_demand": icu_peak_need,
        "vaccine_population_coverage_percent": vaccine_coverage_achieved_percent,
        "diagnostic_sequencing_delay_days": inp.days_to_diagnostic_sequencing,
        "containment_readiness_assessment": (
            "CRITICAL SURGE CAPACITY EXCEEDED: Immediate international COVAX/CEPI vaccine reallocation required."
            if icu_peak_need > 15000
            else "MANAGEABLE HEALTH SYSTEM LOAD: Early diagnostic sequencing and targeted vaccination contain transmission."
        ),
        "treaty_reference": "WHO International Health Regulations (2005) & Global Pandemic Agreement (Article 12 Pathogen Access & Benefit Sharing).",
    }

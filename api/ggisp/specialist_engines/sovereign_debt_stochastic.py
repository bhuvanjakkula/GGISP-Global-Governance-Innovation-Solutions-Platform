"""Specialist Engine 4: Stochastic Sovereign DSA Fan Chart & Haircut Optimization Engine.
Reference: IMF-World Bank Debt Sustainability Framework (DSF) for Market-Access and LICs.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List
from pydantic import BaseModel, Field


from ggisp.specialist_engines.debt_bargaining_game import DebtBargainingInput, simulate_debt_bargaining


class StochasticDSAInput(BaseModel):
    initial_debt_percent_gdp: float = Field(default=82.0, ge=10.0, le=300.0)
    baseline_interest_percent: float = Field(default=6.8, ge=-5.0, le=30.0)
    baseline_growth_percent: float = Field(default=4.5, ge=-15.0, le=25.0)
    primary_surplus_percent: float = Field(default=-0.5, ge=-20.0, le=20.0)
    interest_volatility_sigma: float = Field(default=1.8, ge=0.1, le=10.0)
    growth_volatility_sigma: float = Field(default=2.4, ge=0.1, le=10.0)
    target_sustainable_debt_percent_gdp: float = Field(default=60.0, ge=30.0, le=90.0)
    years: int = Field(default=5, ge=3, le=10)
    monte_carlo_draws: int = Field(default=500, ge=100, le=2000)

    # Advanced Game-Theoretic & Political Economy Parameters (Perera 2026, Flores et al. 2023)
    enable_game_theoretic_bargaining: bool = Field(default=True, description="Continuous-time Nash bargaining between sovereign and creditors (Perera 2026)")
    debtor_bargaining_power_theta: float = Field(default=0.45, ge=0.1, le=0.9, description="Nash bargaining power of sovereign theta in (0, 1)")
    imf_program_liquidity_support_percent_gdp: float = Field(default=6.5, ge=0.0, le=30.0)
    is_preemptive_restructuring: bool = Field(default=True, description="Restructuring executed prior to payment default (Asonuma & Trebesch 2015)")
    incorporate_gdp_indexed_bonds: bool = Field(default=True, description="Link debt service to GDP growth thresholds (Dvorkin et al. 2022)")
    is_election_year: bool = Field(default=True, description="Election cycle proximity introducing upward forecast error (Flores et al. 2023)")


def simulate_stochastic_dsa(inp: StochasticDSAInput) -> Dict[str, Any]:
    """Run pseudo-randomized Monte Carlo simulations to generate debt distribution fan charts and haircut targets."""
    # Seed deterministic pseudo-random sequence for checkable reproducibility
    rng = random.Random(42)
    years = inp.years
    sims: List[List[float]] = []

    for _ in range(inp.monte_carlo_draws):
        d_path = [inp.initial_debt_percent_gdp]
        curr_d = inp.initial_debt_percent_gdp
        for _ in range(1, years + 1):
            i_t = inp.baseline_interest_percent + rng.gauss(0, inp.interest_volatility_sigma)
            g_t = inp.baseline_growth_percent + rng.gauss(0, inp.growth_volatility_sigma)
            i_frac = i_t / 100.0
            g_frac = g_t / 100.0
            pb_t = inp.primary_surplus_percent
            if 1 + g_frac <= 0.05:
                g_frac = 0.05 - 1.0
            curr_d = curr_d * (1 + i_frac) / (1 + g_frac) - pb_t
            curr_d = max(curr_d, 0.0)
            d_path.append(curr_d)
        sims.append(d_path)

    # Compute percentiles for each year (10th, 25th, 50th, 75th, 90th)
    fan_chart = []
    for y in range(years + 1):
        vals = sorted(sims[s][y] for s in range(inp.monte_carlo_draws))
        fan_chart.append({
            "year": y,
            "p10": round(vals[int(len(vals) * 0.10)], 2),
            "p25": round(vals[int(len(vals) * 0.25)], 2),
            "p50_median": round(vals[int(len(vals) * 0.50)], 2),
            "p75": round(vals[int(len(vals) * 0.75)], 2),
            "p90": round(vals[int(len(vals) * 0.90)], 2),
        })

    final_median = fan_chart[-1]["p50_median"]
    target_d = inp.target_sustainable_debt_percent_gdp

    # Haircut estimation: Required reduction in face value to achieve target at Year 5 median
    required_haircut_percent = max(((final_median - target_d) / final_median) * 100.0, 0.0) if final_median > target_d else 0.0
    prob_exceeding_70_percent = sum(1 for s in sims if s[-1] > 70.0) / len(sims) * 100.0

    bargaining_result = None
    if inp.enable_game_theoretic_bargaining:
        bargaining_inp = DebtBargainingInput(
            country_code="SOV",
            outstanding_debt_percent_gdp=inp.initial_debt_percent_gdp,
            debtor_bargaining_power_theta=inp.debtor_bargaining_power_theta,
            imf_program_liquidity_support_percent_gdp=inp.imf_program_liquidity_support_percent_gdp,
            is_preemptive_restructuring=inp.is_preemptive_restructuring,
            incorporate_gdp_indexed_bonds=inp.incorporate_gdp_indexed_bonds,
            is_election_year=inp.is_election_year,
            official_projected_5yr_debt_percent_gdp=final_median,
        )
        bargaining_result = simulate_debt_bargaining(bargaining_inp)

    return {
        "engine": "Stochastic Sovereign DSA Fan Chart & Haircut Optimization Engine",
        "domain": "sovereign-debt",
        "monte_carlo_sample_size": inp.monte_carlo_draws,
        "fan_chart_percentiles": fan_chart,
        "final_year_median_debt_percent_gdp": final_median,
        "probability_of_exceeding_70_percent_gdp": round(prob_exceeding_70_percent, 1),
        "required_npv_haircut_percent_to_reach_target": round(required_haircut_percent, 1),
        "target_sustainable_threshold_percent": target_d,
        "game_theoretic_bargaining": bargaining_result,
        "policy_implication": (
            f"Under current market volatility, the sovereign faces a {round(prob_exceeding_70_percent, 1)}% probability of exceeding critical distress levels. "
            f"A negotiated face-value or coupon-reprofiling debt relief package of {round(required_haircut_percent, 1)}% is mathematically required to anchor debt below {target_d}%."
        ),
        "literature_citations": [
            "Perera, R. S. (2026). Debt, Power, and Play: Modeling Sovereign Restructuring with Creditors and the IMF. Int. J. Financial Engineering, 10.1142/s2424786326500179",
            "Asonuma, T., & Trebesch, C. (2015). Sovereign Debt Restructurings: Preemptive or Post-Default. J. Eur. Econ. Assoc., 10.1111/jeea.12156",
            "Dvorkin, M., Sanchez, J., Sapriza, H., & Yurdagul, E. (2022). Improving Sovereign Debt Restructurings. J. Econ. Dyn. Control, 10.1016/j.jedc.2022.104435",
            "Flores, J., Furceri, D., Kothari, S., & Ostry, J. (2023). Worse than you think: Public debt forecast errors in 174 countries. J. Forecasting, 10.1002/for.2942"
        ]
    }


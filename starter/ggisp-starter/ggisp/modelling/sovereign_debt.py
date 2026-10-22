"""Dynamic Sovereign Debt Sustainability Model with exchange rate & contingent shocks.

Core equation:
d_(t+1) = d_t * (1 + i) / (1 + g) - pb + alpha * delta_e * d_ext + contingent_shock
where:
  d_t: Public debt-to-GDP ratio (%)
  i: Effective nominal interest rate (%)
  g: Nominal GDP growth rate (%)
  pb: Primary budget surplus / net lending (% of GDP)
  alpha * delta_e * d_ext: Currency depreciation valuation effect on foreign-currency debt
  contingent_shock: Realization of contingent liabilities (state guarantees, bank rescues)
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class DynamicDebtAssumptions(BaseModel):
    initial_debt_percent_gdp: float = Field(ge=0.0, le=1000.0, default=75.0)
    interest_rate_percent: float = Field(ge=-20.0, le=100.0, default=6.5)
    nominal_gdp_growth_percent: float = Field(gt=-100.0, le=200.0, default=5.0)
    primary_surplus_percent_gdp: float = Field(ge=-40.0, le=40.0, default=0.0)
    foreign_debt_share_percent: float = Field(ge=0.0, le=100.0, default=50.0)
    currency_depreciation_percent: float = Field(ge=-50.0, le=200.0, default=0.0)
    contingent_liabilities_percent_gdp: float = Field(ge=0.0, le=50.0, default=0.0)
    years: int = Field(ge=1, le=30, default=5)

    @model_validator(mode="after")
    def validate_finite(self):
        values = [
            self.initial_debt_percent_gdp,
            self.interest_rate_percent,
            self.nominal_gdp_growth_percent,
            self.primary_surplus_percent_gdp,
            self.foreign_debt_share_percent,
            self.currency_depreciation_percent,
            self.contingent_liabilities_percent_gdp,
        ]
        if not all(math.isfinite(v) for v in values):
            raise ValueError("All debt model inputs must be finite numbers")
        return self


def simulate_debt(a: DynamicDebtAssumptions) -> Dict[str, Any]:
    """Run dynamic stock-flow debt simulation across multiple analytical scenarios."""
    years = a.years
    scenarios: Dict[str, List[Dict[str, Any]]] = {
        "baseline": [],
        "fiscal_consolidation": [],
        "adverse_shock": [],
        "restructuring_reform": [],
    }

    # 1. Baseline
    d_base = a.initial_debt_percent_gdp
    scenarios["baseline"].append({"year": 0, "debt_percent_gdp": round(d_base, 3)})
    for y in range(1, years + 1):
        # Depreciation effect in year 1
        deprec_effect = (
            (a.foreign_debt_share_percent / 100.0)
            * (a.currency_depreciation_percent / 100.0)
            * d_base
            if y == 1 else 0.0
        )
        cont_shock = a.contingent_liabilities_percent_gdp if y == 1 else 0.0
        d_base = d_base * (1 + a.interest_rate_percent / 100.0) / (1 + a.nominal_gdp_growth_percent / 100.0)
        d_base -= a.primary_surplus_percent_gdp
        d_base += deprec_effect + cont_shock
        scenarios["baseline"].append({"year": y, "debt_percent_gdp": round(max(d_base, 0.0), 3)})

    # 2. Fiscal Consolidation (+1.5% primary surplus per year, but slight growth drag of -0.3%)
    d_consol = a.initial_debt_percent_gdp
    scenarios["fiscal_consolidation"].append({"year": 0, "debt_percent_gdp": round(d_consol, 3)})
    for y in range(1, years + 1):
        pb_reform = a.primary_surplus_percent_gdp + 1.5
        g_drag = a.nominal_gdp_growth_percent - 0.3
        d_consol = d_consol * (1 + a.interest_rate_percent / 100.0) / (1 + g_drag / 100.0)
        d_consol -= pb_reform
        scenarios["fiscal_consolidation"].append({"year": y, "debt_percent_gdp": round(max(d_consol, 0.0), 3)})

    # 3. Adverse Shock (+200bps interest rate, -200bps growth, 15% currency depreciation)
    d_shock = a.initial_debt_percent_gdp
    scenarios["adverse_shock"].append({"year": 0, "debt_percent_gdp": round(d_shock, 3)})
    for y in range(1, years + 1):
        i_shock = a.interest_rate_percent + 2.0
        g_shock = a.nominal_gdp_growth_percent - 2.0
        deprec_shock = (a.foreign_debt_share_percent / 100.0) * (0.15) * d_shock if y == 1 else 0.0
        d_shock = d_shock * (1 + i_shock / 100.0) / (1 + g_shock / 100.0)
        d_shock -= (a.primary_surplus_percent_gdp - 1.0)
        d_shock += deprec_shock
        scenarios["adverse_shock"].append({"year": y, "debt_percent_gdp": round(max(d_shock, 0.0), 3)})

    # 4. Restructuring Reform (20% face-value haircut in year 1, coupon reduced by 250bps, growth protected)
    d_restruct = a.initial_debt_percent_gdp * 0.80  # 20% haircut
    scenarios["restructuring_reform"].append({"year": 0, "debt_percent_gdp": round(d_restruct, 3)})
    for y in range(1, years + 1):
        i_concessional = max(a.interest_rate_percent - 2.5, 1.5)
        g_boost = a.nominal_gdp_growth_percent + 0.5
        d_restruct = d_restruct * (1 + i_concessional / 100.0) / (1 + g_boost / 100.0)
        d_restruct -= a.primary_surplus_percent_gdp
        scenarios["restructuring_reform"].append({"year": y, "debt_percent_gdp": round(max(d_restruct, 0.0), 3)})

    # Debt stabilizing primary balance
    i_frac = a.interest_rate_percent / 100.0
    g_frac = a.nominal_gdp_growth_percent / 100.0
    pb_star = a.initial_debt_percent_gdp * (i_frac - g_frac) / (1 + g_frac) if 1 + g_frac > 0 else 0.0

    return {
        "equation": "d[t+1] = d[t] * (1+i)/(1+g) - pb + (foreign_share * delta_e * d[t]) + contingent_shock",
        "assumptions": a.model_dump(),
        "debt_stabilizing_primary_balance_percent_gdp": round(pb_star, 3),
        "interest_growth_differential": round(a.interest_rate_percent - a.nominal_gdp_growth_percent, 2),
        "scenarios": scenarios,
        "values": scenarios["baseline"],  # backwards compatibility with v0.1
        "disclaimer": "Analytical stock-flow calculation based on sovereign debt accounting identities. Omits endogenous fiscal feedback, capital flight, and non-linear market access closures.",
    }

"""A transparent educational stock-flow debt-ratio illustration.

Equation: d_(t+1) = d_t * (1+i)/(1+g) - pb
where d is debt as percent of GDP; i and g are nominal fractional
interest and GDP growth; pb is a primary SURPLUS in pp of GDP.
This is not a sovereign debt forecast or validated country model.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class DebtAssumptions(BaseModel):
    initial_debt_percent_gdp: float = Field(ge=0, le=1000)
    interest_rate_percent: float = Field(ge=-20, le=100)
    nominal_gdp_growth_percent: float = Field(gt=-100, le=200)
    primary_surplus_percent_gdp: float = Field(ge=-40, le=40)
    years: int = Field(ge=1, le=30)

    @model_validator(mode="after")
    def validate_values(self):
        # JSON parsing already rejects standard non-finite numeric values in FastAPI.
        import math
        values = [self.initial_debt_percent_gdp, self.interest_rate_percent,
                  self.nominal_gdp_growth_percent, self.primary_surplus_percent_gdp]
        if not all(math.isfinite(n) for n in values):
            raise ValueError("Inputs must be finite numbers")
        return self


def simulate(a: DebtAssumptions) -> dict:
    debt = a.initial_debt_percent_gdp
    values = [{"year": 0, "debt_percent_gdp": round(debt, 3)}]
    for year in range(1, a.years + 1):
        debt = debt * (1 + a.interest_rate_percent / 100) / (1 + a.nominal_gdp_growth_percent / 100)
        debt -= a.primary_surplus_percent_gdp
        values.append({"year": year, "debt_percent_gdp": round(debt, 3)})
    return {
        "equation": "d[t+1] = d[t] * (1+i)/(1+g) - primary_surplus",
        "assumptions": a.model_dump(),
        "values": values,
        "disclaimer": "Stylized deterministic illustration only. Not a forecast, valuation, or policy recommendation. Omits exchange-rate, contingent liabilities, stock-flow adjustments and uncertainty.",
    }

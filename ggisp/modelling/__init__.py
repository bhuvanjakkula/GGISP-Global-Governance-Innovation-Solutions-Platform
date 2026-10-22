"""Quantitative policy models for sovereign debt, development finance, and cross-domain simulation."""
import math
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ggisp.modelling.cross_domain import CrossDomainAssumptions, simulate_cross_domain
from ggisp.modelling.development_finance import (
    DevelopmentFinanceAssumptions,
    simulate_development_allocation,
)
from ggisp.modelling.sovereign_debt import (
    DynamicDebtAssumptions,
    simulate_debt,
)


class DebtAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    initial_debt_percent_gdp: float = Field(ge=0, le=1000)
    interest_rate_percent: float = Field(ge=-20, le=100)
    nominal_gdp_growth_percent: float = Field(gt=-100, le=200)
    primary_surplus_percent_gdp: float = Field(ge=-40, le=40)
    years: int = Field(ge=1, le=30)

    @model_validator(mode="after")
    def validate_values(self):
        values = [
            self.initial_debt_percent_gdp,
            self.interest_rate_percent,
            self.nominal_gdp_growth_percent,
            self.primary_surplus_percent_gdp,
        ]
        if not all(math.isfinite(n) for n in values):
            raise ValueError("Inputs must be finite numbers")
        debt = self.initial_debt_percent_gdp
        for _ in range(self.years):
            debt = debt * (1 + self.interest_rate_percent / 100) / (1 + self.nominal_gdp_growth_percent / 100)
            debt -= self.primary_surplus_percent_gdp
            if not math.isfinite(debt) or abs(debt) > 1e12:
                raise ValueError("The trajectory exceeds the model range of ±1e12 percentage points")
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


__all__ = [
    "DebtAssumptions",
    "simulate",
    "DynamicDebtAssumptions",
    "simulate_debt",
    "DevelopmentFinanceAssumptions",
    "simulate_development_allocation",
    "CrossDomainAssumptions",
    "simulate_cross_domain",
]

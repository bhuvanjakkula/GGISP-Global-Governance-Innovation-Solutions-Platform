"""Shared validation types and metadata for analytical engines."""
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

Number = Annotated[float, Field(ge=0, le=1e12, allow_inf_nan=False)]
Percent = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Fraction = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, le=1e12, allow_inf_nan=False)]
Label = Annotated[str, Field(min_length=1, max_length=120)]


class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def unique(items, field="name"):
    values = [getattr(x, field) for x in items]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} values are not allowed")


def entry(domain,title,schema,fn,example,method,limits):
    return dict(domain=domain,title=title,schema=schema,calculate=fn,example=example,
                method=method,limitations=limits,version="1.0.0")



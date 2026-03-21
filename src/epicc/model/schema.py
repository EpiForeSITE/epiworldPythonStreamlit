from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class Author(BaseModel):
    name: str
    email: Optional[EmailStr] = None


class Metadata(BaseModel):
    title: str
    description: str
    authors: list[Author] = Field(default_factory=list)
    introduction: Optional[str] = None


class Parameter(BaseModel):
    type: Literal["integer", "number", "string", "boolean"]
    label: str
    description: Optional[str] = None
    default: int | float | str | bool
    min: Optional[int | float] = None
    max: Optional[int | float] = None
    unit: Optional[str] = None
    references: list[str] = Field(default_factory=list)


class Equation(BaseModel):
    label: str
    unit: Optional[str] = None
    output: Optional[Literal["integer", "number"]] = None
    compute: str = Field(
        ...,
        description="Python-evaluable expression referencing parameter/scenario variable names.",
    )


class ScenarioVars(BaseModel):
    model_config = {"extra": "allow"}  # arbitrary vars like n_cases


class Scenario(BaseModel):
    id: str
    label: str
    vars: ScenarioVars


class TableRow(BaseModel):
    label: str
    value: str = Field(..., description="Key into the equations dict.")
    emphasis: Optional[Literal["strong", "em"]] = None


class Table(BaseModel):
    scenarios: list[Scenario] = Field(default_factory=list)
    rows: list[TableRow] = Field(default_factory=list)


class Figure(BaseModel):
    title: str
    alt_text: Optional[str] = Field(None, alias="alt-text")
    py_code: Optional[str] = Field(None, alias="py-code")

    model_config = {"populate_by_name": True}


class Model(BaseModel):
    metadata: Metadata
    parameters: dict[str, Parameter]
    equations: dict[str, Equation]
    table: Table
    figures: list[Figure] = Field(default_factory=list)


__all__ = ["Model"]

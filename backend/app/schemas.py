"""Pydantic v2 request/response schemas (the API contract)."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---- Auth ----
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# ---- Budgets ----
class BudgetCreate(BaseModel):
    name: str
    fiscal_year: int


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    fiscal_year: int
    created_at: datetime


class BudgetLineCreate(BaseModel):
    category: str
    department: str
    region: str
    planned_amount: float = Field(ge=0)


class BudgetLineOut(BudgetLineCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    budget_id: int


# ---- Variance (budget vs actuals) ----
class VarianceRow(BaseModel):
    dimension: str           # the value being grouped on, e.g. "Engineering"
    planned: float
    actual: float
    variance: float          # actual - planned
    variance_pct: float      # variance / planned * 100


# ---- Scenarios ----
class ScenarioCreate(BaseModel):
    name: str
    description: str = ""


class LeverCreate(BaseModel):
    target_field: Literal["category", "department", "region"]
    target_value: str        # use "*" to target every value of the field
    adjustment_type: Literal["percent", "absolute"]
    adjustment_value: float


class LeverOut(LeverCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    scenario_id: int


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    budget_id: int
    name: str
    description: str
    created_at: datetime
    levers: list[LeverOut] = []


class ScenarioCompareRow(BaseModel):
    dimension: str
    base: float
    scenario: float
    delta: float


class ScenarioCompare(BaseModel):
    group_by: str
    base_total: float
    scenario_total: float
    rows: list[ScenarioCompareRow]

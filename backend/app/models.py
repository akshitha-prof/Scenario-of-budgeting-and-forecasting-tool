"""ORM models for the FP&A domain.

A Budget owns many BudgetLines (planned spend, tagged by department/region/
category). Actuals record what was really spent per period. A Scenario is a
named what-if layered on top of a budget; each Lever adjusts a slice of lines
by a percentage or a flat amount.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="viewer")  # viewer | editor | admin


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="budget", cascade="all, delete-orphan")


class BudgetLine(Base):
    __tablename__ = "budget_lines"
    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    category = Column(String, nullable=False)     # e.g. Headcount, Cloud, Marketing
    department = Column(String, nullable=False)    # e.g. Engineering, Sales
    region = Column(String, nullable=False)        # e.g. APAC, EMEA, AMER
    planned_amount = Column(Float, nullable=False)

    budget = relationship("Budget", back_populates="lines")


class Actual(Base):
    __tablename__ = "actuals"
    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    category = Column(String, nullable=False)
    department = Column(String, nullable=False)
    region = Column(String, nullable=False)
    period = Column(String, nullable=False)        # e.g. 2026-Q1
    actual_amount = Column(Float, nullable=False)


class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    budget = relationship("Budget", back_populates="scenarios")
    levers = relationship("Lever", back_populates="scenario", cascade="all, delete-orphan")


class Lever(Base):
    __tablename__ = "levers"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    # which slice of budget lines this lever targets; "*" means "all values"
    target_field = Column(String, nullable=False)   # category | department | region
    target_value = Column(String, nullable=False)
    adjustment_type = Column(String, nullable=False)  # percent | absolute
    adjustment_value = Column(Float, nullable=False)

    scenario = relationship("Scenario", back_populates="levers")

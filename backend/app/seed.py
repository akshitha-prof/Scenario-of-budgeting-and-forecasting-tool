"""Seed the database with demo users and a sample FY2026 budget.

Run from the backend/ directory:  python -m app.seed
"""
import random

from .database import Base, SessionLocal, engine
from . import models
from .auth import hash_password

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "Operations"]
REGIONS = ["APAC", "EMEA", "AMER"]
CATEGORIES = ["Headcount", "Cloud", "Travel", "Software", "Contractors"]


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # users (username == password for the demo)
        for username, role in [("admin", "admin"), ("analyst", "editor"), ("viewer", "viewer")]:
            db.add(models.User(username=username, password_hash=hash_password(username), role=role))

        budget = models.Budget(name="FY2026 Operating Plan", fiscal_year=2026)
        db.add(budget)
        db.flush()  # get budget.id

        random.seed(42)
        for dept in DEPARTMENTS:
            for region in REGIONS:
                for category in CATEGORIES:
                    planned = random.randint(20, 200) * 1000
                    db.add(models.BudgetLine(
                        budget_id=budget.id, category=category,
                        department=dept, region=region, planned_amount=planned,
                    ))
                    # actuals land within +/-25% of plan
                    actual = planned * random.uniform(0.75, 1.25)
                    db.add(models.Actual(
                        budget_id=budget.id, category=category, department=dept,
                        region=region, period="2026-Q1", actual_amount=round(actual, 2),
                    ))
        db.commit()
        line_count = db.query(models.BudgetLine).count()
        print(f"Seeded budget '{budget.name}' (id={budget.id}) with {line_count} lines + actuals.")
        print("Logins -> admin/admin, analyst/analyst, viewer/viewer")
    finally:
        db.close()


if __name__ == "__main__":
    run()

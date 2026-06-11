"""Test suite: pure-engine unit tests + API/RBAC integration tests.

Uses an isolated SQLite file and FastAPI's TestClient. Run: pytest -q
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Point the app at a throwaway DB before importing it.
_TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP.name}"

from app.database import Base, engine, SessionLocal  # noqa: E402
from app import models  # noqa: E402
from app.auth import hash_password  # noqa: E402
from app.engine import apply_levers, variance, compare_scenario  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.User(username="analyst", password_hash=hash_password("analyst"), role="editor"))
    db.add(models.User(username="viewer", password_hash=hash_password("viewer"), role="viewer"))
    db.commit()
    db.close()
    yield


def token(username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- engine unit tests ----------
def test_apply_percent_lever():
    lines = [{"category": "Cloud", "department": "Eng", "region": "APAC", "planned_amount": 100}]
    levers = [{"target_field": "category", "target_value": "Cloud",
               "adjustment_type": "percent", "adjustment_value": 10}]
    assert apply_levers(lines, levers)[0]["planned_amount"] == pytest.approx(110)


def test_wildcard_absolute_lever_hits_all():
    lines = [{"category": "A", "department": "X", "region": "R", "planned_amount": 100},
             {"category": "B", "department": "Y", "region": "R", "planned_amount": 50}]
    levers = [{"target_field": "department", "target_value": "*",
               "adjustment_type": "absolute", "adjustment_value": 5}]
    out = apply_levers(lines, levers)
    assert [l["planned_amount"] for l in out] == [105, 55]


def test_variance_math():
    planned = [{"department": "Eng", "planned_amount": 100}]
    actual = [{"department": "Eng", "actual_amount": 120}]
    row = variance(planned, actual, "department")[0]
    assert row["variance"] == 20 and row["variance_pct"] == 20.0


def test_compare_scenario_totals():
    base = [{"category": "Cloud", "planned_amount": 100}]
    proj = [{"category": "Cloud", "planned_amount": 130}]
    res = compare_scenario(base, proj, "category")
    assert res["base_total"] == 100 and res["scenario_total"] == 130
    assert res["rows"][0]["delta"] == 30


# ---------- API / RBAC integration tests ----------
def test_login_bad_password():
    r = client.post("/api/auth/login", json={"username": "viewer", "password": "nope"})
    assert r.status_code == 401


def test_protected_endpoint_requires_auth():
    assert client.get("/api/budgets").status_code == 401


def test_viewer_cannot_create_budget():
    r = client.post("/api/budgets", json={"name": "X", "fiscal_year": 2026},
                    headers=auth(token("viewer", "viewer")))
    assert r.status_code == 403


def test_editor_full_scenario_flow():
    tok = token("analyst", "analyst")
    # create a budget
    b = client.post("/api/budgets", json={"name": "FY26", "fiscal_year": 2026}, headers=auth(tok))
    assert b.status_code == 201
    bid = b.json()["id"]
    # add two lines
    for cat, amt in [("Cloud", 1000), ("Travel", 500)]:
        client.post(f"/api/budgets/{bid}/lines",
                    json={"category": cat, "department": "Eng", "region": "APAC", "planned_amount": amt},
                    headers=auth(tok))
    # create scenario + a +20% cloud lever
    s = client.post(f"/api/budgets/{bid}/scenarios", json={"name": "Cloud spike"}, headers=auth(tok))
    sid = s.json()["id"]
    client.post(f"/api/scenarios/{sid}/levers",
                json={"target_field": "category", "target_value": "Cloud",
                      "adjustment_type": "percent", "adjustment_value": 20}, headers=auth(tok))
    cmp = client.get(f"/api/scenarios/{sid}/compare?group_by=category", headers=auth(tok))
    assert cmp.status_code == 200
    body = cmp.json()
    assert body["base_total"] == 1500
    assert body["scenario_total"] == 1700  # cloud 1000 -> 1200

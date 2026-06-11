from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas, engine
from ..auth import get_current_user, require_role
from ..database import get_db

router = APIRouter(prefix="/api", tags=["scenarios"])

GROUPABLE = {"category", "department", "region"}


@router.get("/budgets/{budget_id}/scenarios", response_model=list[schemas.ScenarioOut])
def list_scenarios(budget_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Scenario).filter_by(budget_id=budget_id).all()


@router.post("/budgets/{budget_id}/scenarios", response_model=schemas.ScenarioOut, status_code=201)
def create_scenario(budget_id: int, body: schemas.ScenarioCreate, db: Session = Depends(get_db),
                    _=Depends(require_role("editor"))):
    if not db.get(models.Budget, budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
    scenario = models.Scenario(budget_id=budget_id, **body.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def _get_scenario(scenario_id: int, db: Session) -> models.Scenario:
    scenario = db.get(models.Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/scenarios/{scenario_id}/levers", response_model=schemas.LeverOut, status_code=201)
def add_lever(scenario_id: int, body: schemas.LeverCreate, db: Session = Depends(get_db),
              _=Depends(require_role("editor"))):
    _get_scenario(scenario_id, db)
    lever = models.Lever(scenario_id=scenario_id, **body.model_dump())
    db.add(lever)
    db.commit()
    db.refresh(lever)
    return lever


@router.get("/scenarios/{scenario_id}/compare", response_model=schemas.ScenarioCompare)
def compare(scenario_id: int, group_by: str = Query("category"),
            db: Session = Depends(get_db), _=Depends(get_current_user)):
    if group_by not in GROUPABLE:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {sorted(GROUPABLE)}")
    scenario = _get_scenario(scenario_id, db)
    base = [
        {"category": l.category, "department": l.department, "region": l.region,
         "planned_amount": l.planned_amount}
        for l in db.query(models.BudgetLine).filter_by(budget_id=scenario.budget_id)
    ]
    levers = [
        {"target_field": lv.target_field, "target_value": lv.target_value,
         "adjustment_type": lv.adjustment_type, "adjustment_value": lv.adjustment_value}
        for lv in scenario.levers
    ]
    projected = engine.apply_levers(base, levers)
    return engine.compare_scenario(base, projected, group_by)

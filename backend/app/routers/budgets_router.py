from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas, engine
from ..auth import get_current_user, require_role
from ..database import get_db

router = APIRouter(prefix="/api/budgets", tags=["budgets"])

GROUPABLE = {"category", "department", "region"}


def _get_budget(budget_id: int, db: Session) -> models.Budget:
    budget = db.get(models.Budget, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.get("", response_model=list[schemas.BudgetOut])
def list_budgets(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Budget).order_by(models.Budget.fiscal_year.desc()).all()


@router.post("", response_model=schemas.BudgetOut, status_code=201)
def create_budget(body: schemas.BudgetCreate, db: Session = Depends(get_db),
                  _=Depends(require_role("editor"))):
    budget = models.Budget(**body.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/{budget_id}", response_model=schemas.BudgetOut)
def get_budget(budget_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return _get_budget(budget_id, db)


@router.get("/{budget_id}/lines", response_model=list[schemas.BudgetLineOut])
def list_lines(budget_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    _get_budget(budget_id, db)
    return db.query(models.BudgetLine).filter_by(budget_id=budget_id).all()


@router.post("/{budget_id}/lines", response_model=schemas.BudgetLineOut, status_code=201)
def add_line(budget_id: int, body: schemas.BudgetLineCreate, db: Session = Depends(get_db),
             _=Depends(require_role("editor"))):
    _get_budget(budget_id, db)
    line = models.BudgetLine(budget_id=budget_id, **body.model_dump())
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


@router.get("/{budget_id}/variance", response_model=list[schemas.VarianceRow])
def get_variance(budget_id: int, group_by: str = Query("department"),
                 db: Session = Depends(get_db), _=Depends(get_current_user)):
    if group_by not in GROUPABLE:
        raise HTTPException(status_code=400, detail=f"group_by must be one of {sorted(GROUPABLE)}")
    _get_budget(budget_id, db)
    planned = [
        {"category": l.category, "department": l.department, "region": l.region,
         "planned_amount": l.planned_amount}
        for l in db.query(models.BudgetLine).filter_by(budget_id=budget_id)
    ]
    actuals = [
        {"category": a.category, "department": a.department, "region": a.region,
         "actual_amount": a.actual_amount}
        for a in db.query(models.Actual).filter_by(budget_id=budget_id)
    ]
    return engine.variance(planned, actuals, group_by)

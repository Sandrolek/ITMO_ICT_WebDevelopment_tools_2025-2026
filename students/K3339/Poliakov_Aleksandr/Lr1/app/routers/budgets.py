from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetRead, BudgetReadWithCategory
from app.crud.budget import create_budget, get_budgets_by_user, get_budget, update_budget, delete_budget

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetReadWithCategory])
def list_budgets(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_budgets_by_user(session, current_user.id)


@router.post("", response_model=BudgetRead, status_code=201)
def create(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return create_budget(session, user_id=current_user.id, **data.model_dump())


@router.get("/{budget_id}", response_model=BudgetReadWithCategory)
def get_one(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    budget = get_budget(session, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(404, "Budget not found")
    return budget


@router.patch("/{budget_id}", response_model=BudgetRead)
def update(
    budget_id: int,
    data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    budget = get_budget(session, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(404, "Budget not found")
    return update_budget(session, budget, **data.model_dump(exclude_unset=True))


@router.delete("/{budget_id}")
def delete(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    budget = get_budget(session, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(404, "Budget not found")
    delete_budget(session, budget)
    return {"detail": "deleted"}

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead
from app.crud.category import create_category, get_categories, get_category, update_category, delete_category

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_categories(session)


@router.post("", response_model=CategoryRead, status_code=201)
def create(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return create_category(session, **data.model_dump())


@router.get("/{category_id}", response_model=CategoryRead)
def get_one(
    category_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    category = get_category(session, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update(
    category_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    category = get_category(session, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return update_category(session, category, **data.model_dump(exclude_unset=True))


@router.delete("/{category_id}")
def delete(
    category_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    category = get_category(session, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    delete_category(session, category)
    return {"detail": "deleted"}

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionRead, TransactionReadWithCategories
from app.crud.transaction import (
    create_transaction, get_transactions_by_user, get_transaction, update_transaction, delete_transaction,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionReadWithCategories])
def list_transactions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_transactions_by_user(session, current_user.id)


@router.post("", response_model=TransactionReadWithCategories, status_code=201)
def create(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return create_transaction(
        session,
        user_id=current_user.id,
        category_ids=data.category_ids,
        amount=data.amount,
        description=data.description,
        date=data.date,
        type=data.type,
        account_id=data.account_id,
    )


@router.get("/{transaction_id}", response_model=TransactionReadWithCategories)
def get_one(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txn = get_transaction(session, transaction_id)
    if not txn or txn.user_id != current_user.id:
        raise HTTPException(404, "Transaction not found")
    return txn


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update(
    transaction_id: int,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txn = get_transaction(session, transaction_id)
    if not txn or txn.user_id != current_user.id:
        raise HTTPException(404, "Transaction not found")
    return update_transaction(session, txn, **data.model_dump(exclude_unset=True))


@router.delete("/{transaction_id}")
def delete(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txn = get_transaction(session, transaction_id)
    if not txn or txn.user_id != current_user.id:
        raise HTTPException(404, "Transaction not found")
    delete_transaction(session, txn)
    return {"detail": "deleted"}

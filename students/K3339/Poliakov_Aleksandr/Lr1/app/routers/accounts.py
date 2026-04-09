from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate, AccountRead, AccountReadWithTransactions
from app.crud.account import create_account, get_accounts_by_user, get_account, update_account, delete_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountRead])
def list_accounts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_accounts_by_user(session, current_user.id)


@router.post("", response_model=AccountRead, status_code=201)
def create(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return create_account(session, user_id=current_user.id, **data.model_dump())


@router.get("/{account_id}", response_model=AccountReadWithTransactions)
def get_one(
    account_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    account = get_account(session, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(404, "Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountRead)
def update(
    account_id: int,
    data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    account = get_account(session, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(404, "Account not found")
    return update_account(session, account, **data.model_dump(exclude_unset=True))


@router.delete("/{account_id}")
def delete(
    account_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    account = get_account(session, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(404, "Account not found")
    delete_account(session, account)
    return {"detail": "deleted"}

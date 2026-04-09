from sqlmodel import Session, select
from app.models.account import Account


def create_account(session: Session, user_id: int, **kwargs) -> Account:
    account = Account(user_id=user_id, **kwargs)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def get_accounts_by_user(session: Session, user_id: int) -> list[Account]:
    return list(session.exec(select(Account).where(Account.user_id == user_id)).all())


def get_account(session: Session, account_id: int) -> Account | None:
    return session.get(Account, account_id)


def update_account(session: Session, account: Account, **kwargs) -> Account:
    for key, value in kwargs.items():
        setattr(account, key, value)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def delete_account(session: Session, account: Account) -> None:
    session.delete(account)
    session.commit()

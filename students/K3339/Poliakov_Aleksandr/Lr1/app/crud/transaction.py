from sqlmodel import Session, select
from app.models.transaction import Transaction
from app.models.category import Category


def create_transaction(session: Session, user_id: int, category_ids: list[int], **kwargs) -> Transaction:
    txn = Transaction(user_id=user_id, **kwargs)
    for cat_id in category_ids:
        cat = session.get(Category, cat_id)
        if cat:
            txn.categories.append(cat)
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


def get_transactions_by_user(session: Session, user_id: int) -> list[Transaction]:
    return list(session.exec(select(Transaction).where(Transaction.user_id == user_id)).all())


def get_transaction(session: Session, transaction_id: int) -> Transaction | None:
    return session.get(Transaction, transaction_id)


def update_transaction(session: Session, txn: Transaction, **kwargs) -> Transaction:
    for key, value in kwargs.items():
        setattr(txn, key, value)
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


def delete_transaction(session: Session, txn: Transaction) -> None:
    session.delete(txn)
    session.commit()

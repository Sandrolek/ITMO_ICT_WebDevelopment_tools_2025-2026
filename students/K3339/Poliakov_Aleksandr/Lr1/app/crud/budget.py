from sqlmodel import Session, select
from app.models.budget import Budget


def create_budget(session: Session, user_id: int, **kwargs) -> Budget:
    budget = Budget(user_id=user_id, **kwargs)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


def get_budgets_by_user(session: Session, user_id: int) -> list[Budget]:
    return list(session.exec(select(Budget).where(Budget.user_id == user_id)).all())


def get_budget(session: Session, budget_id: int) -> Budget | None:
    return session.get(Budget, budget_id)


def update_budget(session: Session, budget: Budget, **kwargs) -> Budget:
    for key, value in kwargs.items():
        setattr(budget, key, value)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


def delete_budget(session: Session, budget: Budget) -> None:
    session.delete(budget)
    session.commit()

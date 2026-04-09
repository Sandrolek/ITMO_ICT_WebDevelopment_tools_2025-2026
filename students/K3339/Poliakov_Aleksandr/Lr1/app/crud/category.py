from sqlmodel import Session, select
from app.models.category import Category


def create_category(session: Session, **kwargs) -> Category:
    category = Category(**kwargs)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def get_categories(session: Session) -> list[Category]:
    return list(session.exec(select(Category)).all())


def get_category(session: Session, category_id: int) -> Category | None:
    return session.get(Category, category_id)


def update_category(session: Session, category: Category, **kwargs) -> Category:
    for key, value in kwargs.items():
        setattr(category, key, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category: Category) -> None:
    session.delete(category)
    session.commit()

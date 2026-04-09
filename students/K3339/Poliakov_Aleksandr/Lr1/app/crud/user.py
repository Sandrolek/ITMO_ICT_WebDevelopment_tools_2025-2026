from sqlmodel import Session, select
from app.models.user import User
from app.auth.hashing import hash_password


def create_user(session: Session, username: str, email: str, password: str, **kwargs) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        **kwargs,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.exec(select(User).where(User.username == username)).first()

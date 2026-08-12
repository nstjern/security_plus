"""User persistence."""

from __future__ import annotations

from sqlmodel import Session, select

from app.db.tables import User


def create_user(db: Session, *, username: str, password_hash: str) -> User:
    user = User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.exec(select(User).where(User.username == username)).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_password_hash(db: Session, user: User, password_hash: str) -> None:
    user.password_hash = password_hash
    db.add(user)
    db.commit()

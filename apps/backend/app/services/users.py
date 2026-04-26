from sqlalchemy.orm import Session

from apps.backend.app import crud
from apps.backend.app.models import UserDB


class UserKeyNotFoundError(Exception):
    pass


class IdentityAlreadyLinkedError(Exception):
    pass


def ensure_user_for_identity(
    db: Session,
    provider: str,
    external_id: str,
    name: str | None = None,
) -> UserDB:
    user = crud.get_user_by_identity(db, provider, external_id)
    if user:
        if name and not user.name:
            user.name = name
            db.commit()
            db.refresh(user)
        return user

    user = crud.create_user(db, name=name)
    crud.create_identity(db, user.id, provider, external_id)
    db.refresh(user)
    return user


def link_identity(
    db: Session,
    provider: str,
    external_id: str,
    user_key: str,
) -> UserDB:
    user = crud.get_user_by_key(db, user_key)
    if not user:
        raise UserKeyNotFoundError

    identity = crud.get_identity(db, provider, external_id)
    if identity:
        if identity.user_id != user.id:
            raise IdentityAlreadyLinkedError
        return user

    crud.create_identity(db, user.id, provider, external_id)
    db.refresh(user)
    return user


def get_user_by_key(db: Session, user_key: str) -> UserDB | None:
    return crud.get_user_by_key(db, user_key)

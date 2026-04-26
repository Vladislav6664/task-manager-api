import secrets

from sqlalchemy.orm import Session

from app.models import TaskDB, UserDB, UserIdentityDB
from app.schemas import TaskCreate, TaskUpdate


def _generate_user_key() -> str:
    return f"TM-{secrets.token_hex(4).upper()}"


def create_user(db: Session, name: str | None = None) -> UserDB:
    user = UserDB(name=name, user_key=_generate_user_key())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_key(db: Session, user_key: str) -> UserDB | None:
    return db.query(UserDB).filter(UserDB.user_key == user_key).first()


def get_identity(
    db: Session,
    provider: str,
    external_id: str,
) -> UserIdentityDB | None:
    return (
        db.query(UserIdentityDB)
        .filter(
            UserIdentityDB.provider == provider,
            UserIdentityDB.external_id == external_id,
        )
        .first()
    )


def get_user_by_identity(
    db: Session,
    provider: str,
    external_id: str,
) -> UserDB | None:
    identity = get_identity(db, provider, external_id)
    if not identity:
        return None
    return db.query(UserDB).filter(UserDB.id == identity.user_id).first()


def create_identity(
    db: Session,
    user_id: int,
    provider: str,
    external_id: str,
) -> UserIdentityDB:
    identity = UserIdentityDB(
        user_id=user_id,
        provider=provider,
        external_id=external_id,
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity


def create_task(db: Session, user_id: int, task: TaskCreate) -> TaskDB:
    db_task = TaskDB(
        user_id=user_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        source=task.source,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session, user_id: int, source: str | None = None) -> list[TaskDB]:
    query = db.query(TaskDB).filter(TaskDB.user_id == user_id)
    if source:
        query = query.filter(TaskDB.source == source)
    return query.order_by(TaskDB.id.asc()).all()


def get_task_by_id(db: Session, user_id: int, task_id: int) -> TaskDB | None:
    return (
        db.query(TaskDB)
        .filter(TaskDB.user_id == user_id, TaskDB.id == task_id)
        .first()
    )


def update_task(
    db: Session,
    user_id: int,
    task_id: int,
    updated_task: TaskUpdate,
) -> TaskDB | None:
    db_task = get_task_by_id(db, user_id, task_id)
    if not db_task:
        return None

    db_task.title = updated_task.title
    db_task.description = updated_task.description
    db_task.status = updated_task.status
    db_task.priority = updated_task.priority

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, user_id: int, task_id: int) -> bool:
    db_task = get_task_by_id(db, user_id, task_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True

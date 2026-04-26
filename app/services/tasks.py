from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import TaskDB


def create_task(db: Session, user_id: int, task: schemas.TaskCreate) -> TaskDB:
    return crud.create_task(db, user_id, task)


def list_tasks(
    db: Session,
    user_id: int,
    source: str | None = None,
) -> list[TaskDB]:
    return crud.get_tasks(db, user_id, source=source)


def get_task(db: Session, user_id: int, task_id: int) -> TaskDB | None:
    return crud.get_task_by_id(db, user_id, task_id)


def update_task(
    db: Session,
    user_id: int,
    task_id: int,
    task: schemas.TaskUpdate,
) -> TaskDB | None:
    return crud.update_task(db, user_id, task_id, task)


def delete_task(db: Session, user_id: int, task_id: int) -> bool:
    return crud.delete_task(db, user_id, task_id)


def mark_task_done(db: Session, user_id: int, task_id: int) -> TaskDB | None:
    db_task = crud.get_task_by_id(db, user_id, task_id)
    if not db_task:
        return None

    update_payload = schemas.TaskUpdate(
        title=db_task.title,
        description=db_task.description,
        status="done",
        priority=db_task.priority,
    )
    return crud.update_task(db, user_id, task_id, update_payload)

from sqlalchemy.orm import Session

from app.models import TaskDB
from app.schemas import TaskCreate, TaskUpdate


def create_task(db: Session, task: TaskCreate) -> TaskDB:
    db_task = TaskDB(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session) -> list[TaskDB]:
    return db.query(TaskDB).all()


def get_task_by_id(db: Session, task_id: int) -> TaskDB | None:
    return db.query(TaskDB).filter(TaskDB.id == task_id).first()


def update_task(db: Session, task_id: int, updated_task: TaskUpdate) -> TaskDB | None:
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return None

    db_task.title = updated_task.title
    db_task.description = updated_task.description
    db_task.status = updated_task.status
    db_task.priority = updated_task.priority

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True
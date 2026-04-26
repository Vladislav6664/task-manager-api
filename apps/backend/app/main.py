from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from apps.backend.app import schemas
from apps.backend.app.config import settings
from apps.backend.app.database import initialize_database
from apps.backend.app.dependencies import get_db
from apps.backend.app.services import tasks as task_service
from apps.backend.app.services import users as user_service

initialize_database()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(
    x_user_key: Annotated[str, Header(alias="X-User-Key")],
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_key(db, x_user_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user key")
    return user


@app.post("/users/identify", response_model=schemas.User)
def identify_user(payload: schemas.UserIdentifyRequest, db: Session = Depends(get_db)):
    return user_service.ensure_user_for_identity(
        db,
        provider=payload.provider,
        external_id=payload.external_id,
        name=payload.name,
    )


@app.post("/users/link", response_model=schemas.User)
def link_user_identity(payload: schemas.UserLinkRequest, db: Session = Depends(get_db)):
    try:
        return user_service.link_identity(
            db,
            provider=payload.provider,
            external_id=payload.external_id,
            user_key=payload.user_key,
        )
    except user_service.UserKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User key not found") from exc
    except user_service.IdentityAlreadyLinkedError as exc:
        raise HTTPException(status_code=409, detail="Identity already linked") from exc


@app.get("/users/resolve", response_model=schemas.UserResolveResponse)
def resolve_user_identity(
    provider: schemas.ProviderType,
    external_id: str,
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_identity(db, provider, external_id)
    return schemas.UserResolveResponse(
        provider=provider,
        external_id=external_id,
        linked=user is not None,
        user=user,
    )


@app.get("/users/me", response_model=schemas.User)
def get_current_user_profile(current_user=Depends(get_current_user)):
    return current_user


@app.post("/tasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return task_service.create_task(db, current_user.id, task)


@app.get("/tasks", response_model=list[schemas.Task])
def get_tasks(
    source: schemas.TaskSourceType | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return task_service.list_tasks(db, current_user.id, source=source)


@app.get("/tasks/{task_id}", response_model=schemas.Task)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_task = task_service.get_task(db, current_user.id, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_task = task_service.update_task(db, current_user.id, task_id, task)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = task_service.delete_task(db, current_user.id, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health")
def health_check():
    return {"status": "ok"}

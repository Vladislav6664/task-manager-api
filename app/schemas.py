from pydantic import BaseModel, Field, ConfigDict


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: str = Field(default="new")
    priority: int = Field(default=1, ge=1, le=5)


class TaskUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: str = Field(default="new")
    priority: int = Field(default=1, ge=1, le=5)


class Task(TaskCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
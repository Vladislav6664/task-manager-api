from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProviderType = Literal["telegram", "vk", "web"]
TaskSourceType = Literal["telegram", "vk", "web", "manual"]


class UserIdentifyRequest(BaseModel):
    provider: ProviderType
    external_id: str = Field(..., min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=100)


class UserLinkRequest(BaseModel):
    provider: ProviderType
    external_id: str = Field(..., min_length=1, max_length=100)
    user_key: str = Field(..., min_length=1, max_length=100)


class UserIdentity(BaseModel):
    provider: ProviderType
    external_id: str

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    name: str | None = None
    user_key: str
    identities: list[UserIdentity] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserResolveResponse(BaseModel):
    provider: ProviderType
    external_id: str
    linked: bool
    user: User | None = None


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: str = Field(default="new", max_length=50)
    priority: int = Field(default=1, ge=1, le=5)
    source: TaskSourceType = Field(default="manual")


class TaskUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: str = Field(default="new", max_length=50)
    priority: int = Field(default=1, ge=1, le=5)


class Task(TaskCreate):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

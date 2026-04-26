from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    user_key = Column(String, nullable=False, unique=True, index=True)

    identities = relationship(
        "UserIdentityDB",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tasks = relationship(
        "TaskDB",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserIdentityDB(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_provider_external_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    external_id = Column(String, nullable=False, index=True)

    user = relationship("UserDB", back_populates="identities")


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="new")
    priority = Column(Integer, nullable=False, default=1)
    source = Column(String, nullable=False, default="manual", index=True)

    user = relationship("UserDB", back_populates="tasks")

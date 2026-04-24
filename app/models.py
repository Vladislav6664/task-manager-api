from sqlalchemy import Column, Integer, String

from app.database import Base


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="new")
    priority = Column(Integer, nullable=False, default=1)
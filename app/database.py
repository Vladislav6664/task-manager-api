import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("TASK_MANAGER_DATABASE_URL", "sqlite:///./tasks.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_legacy_schema()


def migrate_legacy_schema() -> None:
    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("tasks")}

    with engine.begin() as connection:
        if "source" not in columns:
            connection.execute(
                text("ALTER TABLE tasks ADD COLUMN source VARCHAR DEFAULT 'manual'")
            )
        if "user_id" not in columns:
            connection.execute(text("ALTER TABLE tasks ADD COLUMN user_id INTEGER"))

        connection.execute(
            text(
                "INSERT OR IGNORE INTO users (name, user_key) "
                "VALUES ('Legacy User', 'TM-LEGACY')"
            )
        )
        connection.execute(
            text(
                "UPDATE tasks SET source = COALESCE(source, 'manual'), "
                "user_id = COALESCE(user_id, (SELECT id FROM users WHERE user_key = 'TM-LEGACY'))"
            )
        )

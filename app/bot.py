import asyncio
from html import escape

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.bot_utils import parse_add_command, parse_task_id
from app.config import settings
from app.database import SessionLocal, initialize_database
from app.services import tasks as task_service
from app.services import users as user_service


HELP_TEXT = (
    "Commands:\n"
    "/tasks - list Telegram tasks\n"
    "/tasks_all - list all your tasks\n"
    "/task <id> - show task\n"
    "/add <title> | <description> | <priority>\n"
    "/done <id> - mark task as done\n"
    "/delete <id> - delete task\n"
    "/key - show your user key for linking VK"
)


def render_task(task) -> str:
    description = task.description or "-"
    return (
        f"#{task.id} {escape(task.title)}\n"
        f"status: {escape(task.status)}\n"
        f"priority: {task.priority}\n"
        f"source: {escape(task.source)}\n"
        f"description: {escape(description)}"
    )


def get_telegram_user(message: Message):
    telegram_user = message.from_user
    if telegram_user is None:
        raise RuntimeError("Telegram user is missing")

    display_name = telegram_user.full_name or telegram_user.username
    with SessionLocal() as db:
        return user_service.ensure_user_for_identity(
            db,
            provider="telegram",
            external_id=str(telegram_user.id),
            name=display_name,
        )


dp = Dispatcher()


@dp.message(Command("start", "help"))
async def start(message: Message) -> None:
    user = get_telegram_user(message)
    await message.answer(
        "Task manager bot is ready.\n"
        "Telegram tasks are separated by source, and you can link VK using your user key.\n\n"
        f"Your user key: {user.user_key}\n\n"
        f"{HELP_TEXT}"
    )


@dp.message(Command("tasks"))
async def list_tasks(message: Message) -> None:
    user = get_telegram_user(message)
    with SessionLocal() as db:
        tasks = task_service.list_tasks(db, user.id, source="telegram")

    if not tasks:
        await message.answer("No Telegram tasks yet.")
        return

    rendered = "\n\n".join(render_task(task) for task in tasks)
    await message.answer(rendered)


@dp.message(Command("tasks_all"))
async def list_all_tasks(message: Message) -> None:
    user = get_telegram_user(message)
    with SessionLocal() as db:
        tasks = task_service.list_tasks(db, user.id)

    if not tasks:
        await message.answer("No tasks yet.")
        return

    rendered = "\n\n".join(render_task(task) for task in tasks)
    await message.answer(rendered)


@dp.message(Command("task"))
async def get_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "task")
    except ValueError as exc:
        await message.answer(str(exc))
        return

    user = get_telegram_user(message)
    with SessionLocal() as db:
        task = task_service.get_task(db, user.id, task_id)

    if not task:
        await message.answer("Task not found.")
        return

    await message.answer(render_task(task))


@dp.message(Command("add"))
async def add_task(message: Message, command: CommandObject) -> None:
    try:
        payload = parse_add_command(command.args)
    except ValueError as exc:
        await message.answer(str(exc))
        return

    user = get_telegram_user(message)
    telegram_payload = payload.model_copy(update={"source": "telegram"})
    with SessionLocal() as db:
        task = task_service.create_task(db, user.id, telegram_payload)

    await message.answer(f"Created task.\n\n{render_task(task)}")


@dp.message(Command("done"))
async def complete_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "done")
    except ValueError as exc:
        await message.answer(str(exc))
        return

    user = get_telegram_user(message)
    with SessionLocal() as db:
        task = task_service.mark_task_done(db, user.id, task_id)

    if not task:
        await message.answer("Task not found.")
        return

    await message.answer(f"Updated task.\n\n{render_task(task)}")


@dp.message(Command("delete"))
async def remove_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "delete")
    except ValueError as exc:
        await message.answer(str(exc))
        return

    user = get_telegram_user(message)
    with SessionLocal() as db:
        deleted = task_service.delete_task(db, user.id, task_id)

    if not deleted:
        await message.answer("Task not found.")
        return

    await message.answer(f"Deleted task #{task_id}.")


@dp.message(Command("key"))
async def show_user_key(message: Message) -> None:
    user = get_telegram_user(message)
    await message.answer(f"Your user key: {user.user_key}")


async def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    initialize_database()
    bot = Bot(token=settings.telegram_bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

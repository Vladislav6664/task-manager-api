import asyncio
from html import escape

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from httpx import HTTPError

from apps.shared.task_manager_client import TaskManagerClient
from apps.telegram_bot.app.bot_utils import parse_add_command, parse_task_id
from apps.telegram_bot.app.config import settings


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

client = TaskManagerClient(settings.backend_api_url)
dp = Dispatcher()


def render_task(task: dict) -> str:
    description = task.get("description") or "-"
    return (
        f"#{task['id']} {escape(task['title'])}\n"
        f"status: {escape(task['status'])}\n"
        f"priority: {task['priority']}\n"
        f"source: {escape(task['source'])}\n"
        f"description: {escape(description)}"
    )


async def ensure_telegram_user(message: Message) -> dict:
    telegram_user = message.from_user
    if telegram_user is None:
        raise RuntimeError("Telegram user is missing")

    display_name = telegram_user.full_name or telegram_user.username
    return await client.identify_user(
        provider="telegram",
        external_id=str(telegram_user.id),
        name=display_name,
    )


async def answer_backend_error(message: Message, exc: HTTPError) -> None:
    await message.answer(f"Backend request failed: {exc}")


@dp.message(Command("start", "help"))
async def start(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(
        "Task manager bot is ready.\n"
        "This bot is a separate client and works through the backend API.\n\n"
        f"Your user key: {user['user_key']}\n\n"
        f"{HELP_TEXT}"
    )


@dp.message(Command("tasks"))
async def list_tasks(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
        tasks = await client.get_tasks(user["user_key"], source="telegram")
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    if not tasks:
        await message.answer("No Telegram tasks yet.")
        return

    await message.answer("\n\n".join(render_task(task) for task in tasks))


@dp.message(Command("tasks_all"))
async def list_all_tasks(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
        tasks = await client.get_tasks(user["user_key"])
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    if not tasks:
        await message.answer("No tasks yet.")
        return

    await message.answer("\n\n".join(render_task(task) for task in tasks))


@dp.message(Command("task"))
async def get_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "task")
        user = await ensure_telegram_user(message)
        task = await client.get_task(user["user_key"], task_id)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(render_task(task))


@dp.message(Command("add"))
async def add_task(message: Message, command: CommandObject) -> None:
    try:
        title, description, priority = parse_add_command(command.args)
        user = await ensure_telegram_user(message)
        task = await client.create_task(
            user_key=user["user_key"],
            title=title,
            description=description,
            priority=priority,
            source="telegram",
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(f"Created task.\n\n{render_task(task)}")


@dp.message(Command("done"))
async def complete_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "done")
        user = await ensure_telegram_user(message)
        task = await client.mark_task_done(user["user_key"], task_id)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(f"Updated task.\n\n{render_task(task)}")


@dp.message(Command("delete"))
async def remove_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "delete")
        user = await ensure_telegram_user(message)
        await client.delete_task(user["user_key"], task_id)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(f"Deleted task #{task_id}.")


@dp.message(Command("key"))
async def show_user_key(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(f"Your user key: {user['user_key']}")


async def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    bot = Bot(token=settings.telegram_bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

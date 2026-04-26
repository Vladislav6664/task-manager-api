import asyncio
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TelegramUser
from httpx import HTTPError

from apps.shared.task_manager_client import TaskManagerClient
from apps.telegram_bot.app.bot_utils import parse_add_command, parse_task_id
from apps.telegram_bot.app.config import settings
from apps.telegram_bot.app.flow_utils import (
    format_task_status,
    normalize_description,
    parse_priority_choice,
    should_keep_current,
)
from apps.telegram_bot.app.keyboards import (
    ALL_TASKS_BUTTON,
    CANCEL_BUTTON,
    CREATE_TASK_BUTTON,
    KEEP_CURRENT_BUTTON,
    SKIP_DESCRIPTION_BUTTON,
    TASKS_BUTTON,
    USER_KEY_BUTTON,
    get_cancel_keyboard,
    get_description_keyboard,
    get_edit_description_keyboard,
    get_edit_priority_keyboard,
    get_keep_current_keyboard,
    get_main_keyboard,
    get_priority_keyboard,
    get_task_actions_keyboard,
)
from apps.telegram_bot.app.states import CreateTaskStates


HELP_TEXT = (
    "Что можно делать:\n"
    "• быстро создавать задачи\n"
    "• смотреть Telegram-задачи отдельно или все сразу\n"
    "• брать задачу в работу, отмечать выполненной, менять и удалять ее кнопками\n"
    "• получать свой user_key для привязки VK\n\n"
    "Если понадобится, команды тоже доступны через /help."
)

client = TaskManagerClient(settings.backend_api_url)
dp = Dispatcher()


def render_task(task: dict) -> str:
    description = task.get("description") or "-"
    return (
        f"#{task['id']} {escape(task['title'])}\n"
        f"статус: {escape(format_task_status(task['status']))}\n"
        f"приоритет: {task['priority']}\n"
        f"источник: {escape(task['source'])}\n"
        f"описание: {escape(description)}"
    )


async def ensure_telegram_user(message: Message) -> dict:
    telegram_user = message.from_user
    if telegram_user is None:
        raise RuntimeError("Не удалось определить пользователя Telegram")

    return await ensure_telegram_identity(telegram_user)


async def ensure_telegram_identity(telegram_user: TelegramUser) -> dict:
    display_name = telegram_user.full_name or telegram_user.username
    return await client.identify_user(
        provider="telegram",
        external_id=str(telegram_user.id),
        name=display_name,
    )


async def answer_backend_error(message: Message, exc: HTTPError) -> None:
    if "404" in str(exc):
        await message.answer("Задача не найдена.", reply_markup=get_main_keyboard())
        return
    await message.answer(
        f"Ошибка запроса к backend: {exc}",
        reply_markup=get_main_keyboard(),
    )


async def send_task_with_actions(message: Message, task: dict) -> None:
    await message.answer(
        render_task(task),
        reply_markup=get_task_actions_keyboard(task["id"]),
    )


async def create_task_for_user(
    message: Message,
    user_key: str,
    title: str,
    description: str | None,
    priority: int,
) -> None:
    task = await client.create_task(
        user_key=user_key,
        title=title,
        description=description,
        priority=priority,
        source="telegram",
    )
    await message.answer("Задача создана.", reply_markup=get_main_keyboard())
    await send_task_with_actions(message, task)


@dp.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        user = await ensure_telegram_user(message)
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    first_name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        f"Привет, {escape(first_name)}.\n"
        "Я помогу быстро записывать и не терять твои задачи.\n\n"
        f"Твой user_key: {user['user_key']}\n\n"
        f"{HELP_TEXT}",
        reply_markup=get_main_keyboard(),
    )


@dp.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/tasks - показать задачи из Telegram\n"
        "/tasks_all - показать все задачи\n"
        "/task <id> - показать задачу по id\n"
        "/add <название> | <описание> | <приоритет>\n"
        "/done <id> - отметить задачу как выполненную\n"
        "/delete <id> - удалить задачу\n"
        "/key - показать user_key для привязки VK",
        reply_markup=get_main_keyboard(),
    )


@dp.message(Command("cancel"))
@dp.message(F.text == CANCEL_BUTTON)
async def cancel_action(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Сейчас нечего отменять.", reply_markup=get_main_keyboard())
        return

    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_main_keyboard())


@dp.message(Command("tasks"))
@dp.message(F.text == TASKS_BUTTON)
async def list_tasks(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
        tasks = await client.get_tasks(user["user_key"], source="telegram")
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    if not tasks:
        await message.answer("У вас пока нет задач из Telegram.", reply_markup=get_main_keyboard())
        return

    await message.answer(f"Найдено задач: {len(tasks)}", reply_markup=get_main_keyboard())
    for task in tasks:
        await send_task_with_actions(message, task)


@dp.message(Command("tasks_all"))
@dp.message(F.text == ALL_TASKS_BUTTON)
async def list_all_tasks(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
        tasks = await client.get_tasks(user["user_key"])
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    if not tasks:
        await message.answer("У вас пока нет задач.", reply_markup=get_main_keyboard())
        return

    await message.answer(f"Найдено задач: {len(tasks)}", reply_markup=get_main_keyboard())
    for task in tasks:
        await send_task_with_actions(message, task)


@dp.message(Command("task"))
async def get_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "task")
        user = await ensure_telegram_user(message)
        task = await client.get_task(user["user_key"], task_id)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=get_main_keyboard())
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await send_task_with_actions(message, task)


@dp.message(Command("add"))
async def add_task(message: Message, command: CommandObject) -> None:
    try:
        title, description, priority = parse_add_command(command.args)
        user = await ensure_telegram_user(message)
        await create_task_for_user(message, user["user_key"], title, description, priority)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=get_main_keyboard())
    except HTTPError as exc:
        await answer_backend_error(message, exc)


@dp.message(F.text == CREATE_TASK_BUTTON)
async def start_create_task_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CreateTaskStates.waiting_for_title)
    await message.answer(
        "Введите название задачи.",
        reply_markup=get_cancel_keyboard(),
    )


@dp.message(CreateTaskStates.waiting_for_title)
async def receive_task_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым. Введите название задачи.")
        return

    await state.update_data(title=title)
    await state.set_state(CreateTaskStates.waiting_for_description)
    await message.answer(
        "Введите описание задачи или нажмите «Без описания».",
        reply_markup=get_description_keyboard(),
    )


@dp.message(CreateTaskStates.waiting_for_description)
async def receive_task_description(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    description = normalize_description(text)

    await state.update_data(description=description)
    await state.set_state(CreateTaskStates.waiting_for_priority)
    await message.answer(
        "Выберите приоритет задачи от 1 до 5.",
        reply_markup=get_priority_keyboard(),
    )


@dp.message(CreateTaskStates.waiting_for_priority)
async def receive_task_priority(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    try:
        priority = parse_priority_choice(text)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=get_priority_keyboard())
        return

    data = await state.get_data()
    await state.clear()

    try:
        user = await ensure_telegram_user(message)
        await create_task_for_user(
            message,
            user["user_key"],
            data["title"],
            data.get("description"),
            priority,
        )
    except HTTPError as exc:
        await answer_backend_error(message, exc)


@dp.message(CreateTaskStates.waiting_for_edit_title)
async def receive_edit_title(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if should_keep_current(text):
        data = await state.get_data()
        title = data["current_title"]
    else:
        title = text.strip()

    if not title:
        await message.answer("Название не должно быть пустым. Введите новое название задачи.")
        return

    await state.update_data(edit_title=title)
    await state.set_state(CreateTaskStates.waiting_for_edit_description)
    await message.answer(
        "Введите новое описание, нажмите «Без описания» или «Оставить как есть».",
        reply_markup=get_edit_description_keyboard(),
    )


@dp.message(CreateTaskStates.waiting_for_edit_description)
async def receive_edit_description(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if should_keep_current(text):
        data = await state.get_data()
        description = data.get("current_description")
    else:
        description = normalize_description(text)

    await state.update_data(edit_description=description)
    await state.set_state(CreateTaskStates.waiting_for_edit_priority)
    await message.answer(
        "Выберите новый приоритет от 1 до 5 или нажмите «Оставить как есть».",
        reply_markup=get_edit_priority_keyboard(),
    )


@dp.message(CreateTaskStates.waiting_for_edit_priority)
async def receive_edit_priority(message: Message, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        if should_keep_current(message.text or ""):
            priority = data["current_priority"]
        else:
            priority = parse_priority_choice(message.text or "")
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=get_edit_priority_keyboard())
        return

    task_id = data.get("edit_task_id")
    await state.clear()

    try:
        user = await ensure_telegram_user(message)
        task = await client.update_task(
            user_key=user["user_key"],
            task_id=task_id,
            title=data["edit_title"],
            description=data.get("edit_description"),
            status=data["edit_task_status"],
            priority=priority,
        )
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer("Задача изменена.", reply_markup=get_main_keyboard())
    await send_task_with_actions(message, task)


@dp.message(Command("done"))
async def complete_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "done")
        user = await ensure_telegram_user(message)
        task = await client.mark_task_done(user["user_key"], task_id)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=get_main_keyboard())
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer("Задача отмечена как выполненная.", reply_markup=get_main_keyboard())
    await send_task_with_actions(message, task)


@dp.message(Command("delete"))
async def remove_task(message: Message, command: CommandObject) -> None:
    try:
        task_id = parse_task_id(command.args, "delete")
        user = await ensure_telegram_user(message)
        await client.delete_task(user["user_key"], task_id)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=get_main_keyboard())
        return
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(f"Задача #{task_id} удалена.", reply_markup=get_main_keyboard())


@dp.callback_query(F.data.startswith("done:"))
async def done_task_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer("Не удалось обновить задачу.", show_alert=True)
        return

    task_id = int(callback.data.split(":", 1)[1])
    try:
        user = await ensure_telegram_identity(callback.from_user)
        task = await client.mark_task_done(user["user_key"], task_id)
    except HTTPError as exc:
        if "404" in str(exc):
            await callback.answer("Задача не найдена.", show_alert=True)
        else:
            await callback.answer("Ошибка обновления задачи.", show_alert=True)
        return

    await callback.answer("Готово")
    await callback.message.edit_text(render_task(task), reply_markup=get_task_actions_keyboard(task_id))


@dp.callback_query(F.data.startswith("progress:"))
async def progress_task_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer("Не удалось обновить задачу.", show_alert=True)
        return

    task_id = int(callback.data.split(":", 1)[1])
    try:
        user = await ensure_telegram_identity(callback.from_user)
        current_task = await client.get_task(user["user_key"], task_id)
        task = await client.update_task(
            user_key=user["user_key"],
            task_id=task_id,
            title=current_task["title"],
            description=current_task["description"],
            status="in_progress",
            priority=current_task["priority"],
        )
    except HTTPError as exc:
        if "404" in str(exc):
            await callback.answer("Задача не найдена.", show_alert=True)
        else:
            await callback.answer("Ошибка обновления задачи.", show_alert=True)
        return

    await callback.answer("В работе")
    await callback.message.edit_text(render_task(task), reply_markup=get_task_actions_keyboard(task_id))


@dp.callback_query(F.data.startswith("edit:"))
async def edit_task_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer("Не удалось перейти к изменению.", show_alert=True)
        return

    task_id = int(callback.data.split(":", 1)[1])
    try:
        user = await ensure_telegram_identity(callback.from_user)
        task = await client.get_task(user["user_key"], task_id)
    except HTTPError as exc:
        if "404" in str(exc):
            await callback.answer("Задача не найдена.", show_alert=True)
        else:
            await callback.answer("Ошибка загрузки задачи.", show_alert=True)
        return

    await state.set_state(CreateTaskStates.waiting_for_edit_title)
    await state.update_data(
        edit_task_id=task_id,
        edit_task_status=task["status"],
        current_title=task["title"],
        current_description=task.get("description"),
        current_priority=task["priority"],
    )
    await callback.answer("Начинаем изменение")
    await callback.message.answer(
        "Введите новое название задачи или нажмите «Оставить как есть».",
        reply_markup=get_keep_current_keyboard(),
    )


@dp.callback_query(F.data.startswith("delete:"))
async def delete_task_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer("Не удалось удалить задачу.", show_alert=True)
        return

    task_id = int(callback.data.split(":", 1)[1])
    try:
        user = await ensure_telegram_identity(callback.from_user)
        await client.delete_task(user["user_key"], task_id)
    except HTTPError as exc:
        if "404" in str(exc):
            await callback.answer("Задача уже удалена.", show_alert=True)
        else:
            await callback.answer("Ошибка удаления задачи.", show_alert=True)
        return

    await callback.answer("Задача удалена.")
    await callback.message.edit_text(f"Задача #{task_id} удалена.")


@dp.message(Command("key"))
@dp.message(F.text == USER_KEY_BUTTON)
async def show_user_key(message: Message) -> None:
    try:
        user = await ensure_telegram_user(message)
    except HTTPError as exc:
        await answer_backend_error(message, exc)
        return

    await message.answer(
        f"Ваш user_key: {user['user_key']}",
        reply_markup=get_main_keyboard(),
    )


@dp.message(F.text == SKIP_DESCRIPTION_BUTTON)
async def handle_skip_description_outside_flow(message: Message) -> None:
    await message.answer(
        "Кнопка «Без описания» работает только во время создания задачи.",
        reply_markup=get_main_keyboard(),
    )


@dp.message(F.text == KEEP_CURRENT_BUTTON)
async def handle_keep_current_outside_flow(message: Message) -> None:
    await message.answer(
        "Кнопка «Оставить как есть» работает только во время изменения задачи.",
        reply_markup=get_main_keyboard(),
    )


@dp.message()
async def fallback_message(message: Message) -> None:
    await message.answer(
        "Нажмите кнопку ниже или используйте /help, если нужен список команд.",
        reply_markup=get_main_keyboard(),
    )


async def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")

    bot = Bot(token=settings.telegram_bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


CREATE_TASK_BUTTON = "Создать"
TASKS_BUTTON = "Telegram"
ALL_TASKS_BUTTON = "Все мои"
USER_KEY_BUTTON = "Ключ"
CANCEL_BUTTON = "Отмена"
SKIP_DESCRIPTION_BUTTON = "Без описания"
KEEP_CURRENT_BUTTON = "Оставить как есть"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CREATE_TASK_BUTTON), KeyboardButton(text=TASKS_BUTTON)],
            [KeyboardButton(text=ALL_TASKS_BUTTON), KeyboardButton(text=USER_KEY_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
        resize_keyboard=True,
    )


def get_description_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_DESCRIPTION_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_keep_current_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=KEEP_CURRENT_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_edit_description_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=KEEP_CURRENT_BUTTON), KeyboardButton(text=SKIP_DESCRIPTION_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_priority_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5")],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_edit_priority_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5")],
            [KeyboardButton(text=KEEP_CURRENT_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="В работу", callback_data=f"progress:{task_id}"),
                InlineKeyboardButton(text="Готово", callback_data=f"done:{task_id}"),
                InlineKeyboardButton(text="Изменить", callback_data=f"edit:{task_id}"),
                InlineKeyboardButton(text="Удалить", callback_data=f"delete:{task_id}"),
            ]
        ]
    )

from apps.telegram_bot.app.keyboards import KEEP_CURRENT_BUTTON, SKIP_DESCRIPTION_BUTTON


def normalize_description(text: str) -> str | None:
    cleaned = text.strip()
    if not cleaned or cleaned == SKIP_DESCRIPTION_BUTTON:
        return None
    return cleaned


def should_keep_current(text: str) -> bool:
    return text.strip() == KEEP_CURRENT_BUTTON


def parse_priority_choice(text: str) -> int:
    cleaned = text.strip()
    if cleaned not in {"1", "2", "3", "4", "5"}:
        raise ValueError("Приоритет должен быть числом от 1 до 5.")
    return int(cleaned)


def format_task_status(status: str) -> str:
    status_map = {
        "new": "Новая",
        "in_progress": "В работе",
        "done": "Выполнено",
    }
    return status_map.get(status, status)

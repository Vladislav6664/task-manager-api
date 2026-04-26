import pytest

from apps.telegram_bot.app.bot_utils import parse_add_command, parse_task_id


def test_parse_add_command_with_all_fields():
    title, description, priority = parse_add_command("Ship bot | Telegram client | 4")

    assert title == "Ship bot"
    assert description == "Telegram client"
    assert priority == 4


def test_parse_add_command_with_title_only():
    title, description, priority = parse_add_command("Ship frontend")

    assert title == "Ship frontend"
    assert description is None
    assert priority == 1


def test_parse_task_id_rejects_invalid_value():
    with pytest.raises(ValueError, match="integer"):
        parse_task_id("abc", "task")

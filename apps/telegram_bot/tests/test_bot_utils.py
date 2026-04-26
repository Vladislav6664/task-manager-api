import pytest

from apps.telegram_bot.app.bot_utils import parse_add_command, parse_task_id
from apps.telegram_bot.app.flow_utils import (
    format_task_status,
    normalize_description,
    parse_priority_choice,
    should_keep_current,
)


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
    with pytest.raises(ValueError, match="целым числом"):
        parse_task_id("abc", "task")


def test_normalize_description_skips_special_button():
    assert normalize_description("Без описания") is None


def test_parse_priority_choice_rejects_out_of_range_value():
    with pytest.raises(ValueError, match="от 1 до 5"):
        parse_priority_choice("8")


def test_format_task_status_for_done():
    assert format_task_status("done") == "Выполнено"


def test_should_keep_current_button():
    assert should_keep_current("Оставить как есть") is True

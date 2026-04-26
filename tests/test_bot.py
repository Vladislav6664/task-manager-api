import pytest

from app.bot_utils import parse_add_command, parse_task_id


def test_parse_add_command_with_all_fields():
    task = parse_add_command("Ship bot | Telegram client | 4")

    assert task.title == "Ship bot"
    assert task.description == "Telegram client"
    assert task.priority == 4
    assert task.status == "new"


def test_parse_add_command_with_title_only():
    task = parse_add_command("Ship frontend")

    assert task.title == "Ship frontend"
    assert task.description is None
    assert task.priority == 1


def test_parse_task_id_rejects_invalid_value():
    with pytest.raises(ValueError, match="integer"):
        parse_task_id("abc", "task")

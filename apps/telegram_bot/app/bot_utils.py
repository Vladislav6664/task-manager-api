def parse_add_command(arguments: str | None) -> tuple[str, str | None, int]:
    if not arguments:
        raise ValueError("Использование: /add <название> | <описание> | <приоритет>")

    parts = [part.strip() for part in arguments.split("|")]
    if len(parts) not in {1, 2, 3}:
        raise ValueError("Использование: /add <название> | <описание> | <приоритет>")

    title = parts[0]
    description = parts[1] if len(parts) >= 2 and parts[1] else None
    priority = int(parts[2]) if len(parts) == 3 and parts[2] else 1
    return title, description, priority


def parse_task_id(arguments: str | None, command_name: str) -> int:
    if not arguments:
        raise ValueError(f"Использование: /{command_name} <id>")

    try:
        return int(arguments.strip())
    except ValueError as exc:
        raise ValueError("ID задачи должен быть целым числом") from exc

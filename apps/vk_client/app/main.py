import argparse
import asyncio
import json

from apps.shared.task_manager_client import TaskManagerClient
from apps.vk_client.app.config import settings


client = TaskManagerClient(settings.backend_api_url)


async def identify_vk_user(vk_id: str, name: str | None) -> None:
    user = await client.identify_user("vk", vk_id, name)
    print(json.dumps(user, ensure_ascii=False, indent=2))


async def link_vk_user(vk_id: str, user_key: str) -> None:
    user = await client.link_user("vk", vk_id, user_key)
    print(json.dumps(user, ensure_ascii=False, indent=2))


async def list_tasks(user_key: str, source: str | None) -> None:
    tasks = await client.get_tasks(user_key, source=source)
    print(json.dumps(tasks, ensure_ascii=False, indent=2))


async def create_task(user_key: str, title: str, description: str | None, priority: int) -> None:
    task = await client.create_task(
        user_key=user_key,
        title=title,
        description=description,
        priority=priority,
        source="vk",
    )
    print(json.dumps(task, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VK client for Task Manager backend")
    subparsers = parser.add_subparsers(dest="command", required=True)

    identify_parser = subparsers.add_parser("identify", help="Create or fetch VK user")
    identify_parser.add_argument("--vk-id", required=True)
    identify_parser.add_argument("--name")

    link_parser = subparsers.add_parser("link", help="Link VK identity to existing user_key")
    link_parser.add_argument("--vk-id", required=True)
    link_parser.add_argument("--user-key", required=True)

    tasks_parser = subparsers.add_parser("tasks", help="List tasks for linked user")
    tasks_parser.add_argument("--user-key", required=True)
    tasks_parser.add_argument("--source")

    add_parser = subparsers.add_parser("add", help="Create VK task through backend")
    add_parser.add_argument("--user-key", required=True)
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--description")
    add_parser.add_argument("--priority", type=int, default=1)

    return parser


async def dispatch(args: argparse.Namespace) -> None:
    if args.command == "identify":
        await identify_vk_user(args.vk_id, args.name)
    elif args.command == "link":
        await link_vk_user(args.vk_id, args.user_key)
    elif args.command == "tasks":
        await list_tasks(args.user_key, args.source)
    elif args.command == "add":
        await create_task(args.user_key, args.title, args.description, args.priority)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(dispatch(args))


if __name__ == "__main__":
    main()

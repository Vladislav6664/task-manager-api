import argparse
import asyncio
import json

from apps.shared.task_manager_client import TaskManagerClient
from apps.vk_client.app.config import settings
from apps.vk_client.app.session_store import VkSessionStore


client = TaskManagerClient(settings.backend_api_url)
session_store = VkSessionStore(settings.session_path)


def print_json(data: dict | list[dict]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def identify_vk_user(vk_id: str, name: str | None) -> None:
    user = await client.identify_user("vk", vk_id, name)
    session_store.update(vk_id=vk_id, user_key=user["user_key"])
    print_json(user)


async def link_vk_user(vk_id: str, user_key: str) -> None:
    user = await client.link_user("vk", vk_id, user_key)
    session_store.update(vk_id=vk_id, user_key=user["user_key"])
    print_json(user)


async def list_tasks(user_key: str, source: str | None) -> None:
    tasks = await client.get_tasks(user_key, source=source)
    print_json(tasks)


async def create_task(user_key: str, title: str, description: str | None, priority: int) -> None:
    task = await client.create_task(
        user_key=user_key,
        title=title,
        description=description,
        priority=priority,
        source="vk",
    )
    print_json(task)


async def resolve_vk_user(vk_id: str) -> None:
    result = await client.resolve_user("vk", vk_id)
    if result["linked"] and result["user"]:
        session_store.update(vk_id=vk_id, user_key=result["user"]["user_key"])
    print_json(result)


async def onboard_vk_user(vk_id: str, name: str | None) -> None:
    result = await client.resolve_user("vk", vk_id)

    if result["linked"]:
        user = result["user"]
        session_store.update(vk_id=vk_id, user_key=user["user_key"])
        print("VK account is already linked.")
        print_json(user)
        print("\nVK tasks:")
        tasks = await client.get_tasks(user["user_key"], source="vk")
        print_json(tasks)
        return

    print("VK account is not linked yet.")
    print("Options:")
    print("1. Enter an existing user_key from Telegram to link accounts.")
    print("2. Press Enter without a key to create a separate VK-only account.")

    user_key = input("Enter user_key (or leave empty to create a new VK account): ").strip()

    if user_key:
        user = await client.link_user("vk", vk_id, user_key)
        session_store.update(vk_id=vk_id, user_key=user["user_key"])
        print("\nVK account linked to existing user:")
        print_json(user)
        return

    user = await client.identify_user("vk", vk_id, name)
    session_store.update(vk_id=vk_id, user_key=user["user_key"])
    print("\nCreated a standalone VK user:")
    print_json(user)


def resolve_runtime_vk_id(vk_id: str | None) -> str:
    if vk_id:
        return vk_id

    stored_vk_id = session_store.load().get("vk_id") or settings.vk_external_id
    if stored_vk_id:
        return stored_vk_id

    raise ValueError("VK id is required. Pass --vk-id or set VK_EXTERNAL_ID in .env.")


def resolve_runtime_user_key(user_key: str | None) -> str:
    if user_key:
        return user_key

    stored_user_key = session_store.load().get("user_key")
    if stored_user_key:
        return stored_user_key

    raise ValueError("user_key is required. Run onboard/link first or pass --user-key.")


def show_session() -> None:
    print_json(session_store.load())


def clear_session() -> None:
    session_store.clear()
    print("VK client session cleared.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VK client for Task Manager backend")
    subparsers = parser.add_subparsers(dest="command", required=True)

    identify_parser = subparsers.add_parser("identify", help="Create or fetch VK user directly")
    identify_parser.add_argument("--vk-id")
    identify_parser.add_argument("--name")

    resolve_parser = subparsers.add_parser("resolve", help="Check whether VK identity is already linked")
    resolve_parser.add_argument("--vk-id")

    onboard_parser = subparsers.add_parser("onboard", help="Realistic VK onboarding flow")
    onboard_parser.add_argument("--vk-id")
    onboard_parser.add_argument("--name")

    link_parser = subparsers.add_parser("link", help="Link VK identity to existing user_key")
    link_parser.add_argument("--vk-id")
    link_parser.add_argument("--user-key")

    tasks_parser = subparsers.add_parser("tasks", help="List tasks for linked user")
    tasks_parser.add_argument("--user-key")
    tasks_parser.add_argument("--source")

    add_parser = subparsers.add_parser("add", help="Create VK task through backend")
    add_parser.add_argument("--user-key")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--description")
    add_parser.add_argument("--priority", type=int, default=1)

    subparsers.add_parser("session", help="Show saved VK client session")
    subparsers.add_parser("clear-session", help="Clear saved VK client session")

    return parser


async def dispatch(args: argparse.Namespace) -> None:
    if args.command == "identify":
        await identify_vk_user(resolve_runtime_vk_id(args.vk_id), args.name)
    elif args.command == "resolve":
        await resolve_vk_user(resolve_runtime_vk_id(args.vk_id))
    elif args.command == "onboard":
        await onboard_vk_user(resolve_runtime_vk_id(args.vk_id), args.name)
    elif args.command == "link":
        await link_vk_user(
            resolve_runtime_vk_id(args.vk_id),
            resolve_runtime_user_key(args.user_key),
        )
    elif args.command == "tasks":
        await list_tasks(resolve_runtime_user_key(args.user_key), args.source)
    elif args.command == "add":
        await create_task(
            resolve_runtime_user_key(args.user_key),
            args.title,
            args.description,
            args.priority,
        )
    elif args.command == "session":
        show_session()
    elif args.command == "clear-session":
        clear_session()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        asyncio.run(dispatch(args))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()

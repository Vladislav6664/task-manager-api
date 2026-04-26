import os

import httpx


class TaskManagerClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")).rstrip("/")

    async def identify_user(
        self,
        provider: str,
        external_id: str,
        name: str | None = None,
    ) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/users/identify",
                json={
                    "provider": provider,
                    "external_id": external_id,
                    "name": name,
                },
            )
            response.raise_for_status()
            return response.json()

    async def resolve_user(
        self,
        provider: str,
        external_id: str,
    ) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                "/users/resolve",
                params={
                    "provider": provider,
                    "external_id": external_id,
                },
            )
            response.raise_for_status()
            return response.json()

    async def link_user(
        self,
        provider: str,
        external_id: str,
        user_key: str,
    ) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/users/link",
                json={
                    "provider": provider,
                    "external_id": external_id,
                    "user_key": user_key,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_me(self, user_key: str) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                "/users/me",
                headers={"X-User-Key": user_key},
            )
            response.raise_for_status()
            return response.json()

    async def get_tasks(self, user_key: str, source: str | None = None) -> list[dict]:
        params = {"source": source} if source else None
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                "/tasks",
                headers={"X-User-Key": user_key},
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def get_task(self, user_key: str, task_id: int) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"/tasks/{task_id}",
                headers={"X-User-Key": user_key},
            )
            response.raise_for_status()
            return response.json()

    async def create_task(
        self,
        user_key: str,
        title: str,
        description: str | None = None,
        priority: int = 1,
        status: str = "new",
        source: str = "manual",
    ) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/tasks",
                headers={"X-User-Key": user_key},
                json={
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                    "source": source,
                },
            )
            response.raise_for_status()
            return response.json()

    async def update_task(
        self,
        user_key: str,
        task_id: int,
        title: str,
        description: str | None,
        status: str,
        priority: int,
    ) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"/tasks/{task_id}",
                headers={"X-User-Key": user_key},
                json={
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                },
            )
            response.raise_for_status()
            return response.json()

    async def mark_task_done(self, user_key: str, task_id: int) -> dict:
        task = await self.get_task(user_key, task_id)
        return await self.update_task(
            user_key=user_key,
            task_id=task_id,
            title=task["title"],
            description=task["description"],
            status="done",
            priority=task["priority"],
        )

    async def delete_task(self, user_key: str, task_id: int) -> None:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(
                f"/tasks/{task_id}",
                headers={"X-User-Key": user_key},
            )
            response.raise_for_status()

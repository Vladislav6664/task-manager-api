from apps.backend.app.schemas import TaskCreate
from apps.backend.app.services import tasks as task_service
from apps.backend.app.services import users as user_service


def create_user(client, provider="web", external_id="web-user-1", name="Test User"):
    response = client.post(
        "/users/identify",
        json={
            "provider": provider,
            "external_id": external_id,
            "name": name,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_identify_user_returns_stable_user_key(client):
    first = create_user(client, provider="telegram", external_id="1001", name="Alice")
    second = create_user(client, provider="telegram", external_id="1001", name="Alice")

    assert first["id"] == second["id"]
    assert first["user_key"] == second["user_key"]
    assert first["identities"][0]["provider"] == "telegram"


def test_link_vk_identity_to_existing_user(client):
    user = create_user(client, provider="telegram", external_id="1002", name="Bob")

    response = client.post(
        "/users/link",
        json={
            "provider": "vk",
            "external_id": "vk-2002",
            "user_key": user["user_key"],
        },
    )

    assert response.status_code == 200
    providers = {identity["provider"] for identity in response.json()["identities"]}
    assert providers == {"telegram", "vk"}


def test_get_current_user_profile(client):
    user = create_user(client, provider="web", external_id="web-me")

    response = client.get("/users/me", headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 200
    assert response.json()["user_key"] == user["user_key"]


def test_create_task(client):
    user = create_user(client)
    payload = {
        "title": "Learn pytest",
        "description": "Write API tests",
        "status": "new",
        "priority": 1,
        "source": "web",
    }

    response = client.post("/tasks", json=payload, headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["user_id"] == user["id"]
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["status"] == payload["status"]
    assert data["priority"] == payload["priority"]
    assert data["source"] == payload["source"]


def test_get_tasks_returns_only_current_user_tasks(client):
    first_user = create_user(client, external_id="web-user-a")
    second_user = create_user(client, external_id="web-user-b")

    client.post(
        "/tasks",
        json={"title": "A", "description": "One", "status": "new", "priority": 2, "source": "web"},
        headers={"X-User-Key": first_user["user_key"]},
    )
    client.post(
        "/tasks",
        json={"title": "B", "description": "Two", "status": "new", "priority": 3, "source": "telegram"},
        headers={"X-User-Key": second_user["user_key"]},
    )

    response = client.get("/tasks", headers={"X-User-Key": first_user["user_key"]})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "A"
    assert data[0]["user_id"] == first_user["id"]


def test_get_tasks_by_source(client):
    user = create_user(client, external_id="web-user-filter")

    client.post(
        "/tasks",
        json={"title": "Web task", "description": "From web", "status": "new", "priority": 2, "source": "web"},
        headers={"X-User-Key": user["user_key"]},
    )
    client.post(
        "/tasks",
        json={"title": "VK task", "description": "From vk", "status": "new", "priority": 3, "source": "vk"},
        headers={"X-User-Key": user["user_key"]},
    )

    response = client.get("/tasks?source=vk", headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source"] == "vk"


def test_get_task_by_id(client):
    user = create_user(client, external_id="web-user-find")
    payload = {
        "title": "Find me",
        "description": "Task by id",
        "status": "new",
        "priority": 3,
        "source": "web",
    }

    create_response = client.post("/tasks", json=payload, headers={"X-User-Key": user["user_key"]})
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == payload["title"]


def test_get_task_of_another_user_returns_404(client):
    first_user = create_user(client, external_id="owner")
    second_user = create_user(client, external_id="outsider")
    payload = {
        "title": "Private task",
        "description": "Hidden",
        "status": "new",
        "priority": 2,
        "source": "web",
    }

    create_response = client.post("/tasks", json=payload, headers={"X-User-Key": first_user["user_key"]})
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers={"X-User-Key": second_user["user_key"]})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task(client):
    user = create_user(client, external_id="update-user")
    create_payload = {
        "title": "Old title",
        "description": "Old description",
        "status": "new",
        "priority": 1,
        "source": "web",
    }

    create_response = client.post("/tasks", json=create_payload, headers={"X-User-Key": user["user_key"]})
    task_id = create_response.json()["id"]

    update_payload = {
        "title": "Updated title",
        "description": "Updated description",
        "status": "in_progress",
        "priority": 3,
    }

    response = client.put(
        f"/tasks/{task_id}",
        json=update_payload,
        headers={"X-User-Key": user["user_key"]},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == update_payload["title"]
    assert data["description"] == update_payload["description"]
    assert data["status"] == update_payload["status"]
    assert data["priority"] == update_payload["priority"]
    assert data["source"] == "web"


def test_delete_task(client):
    user = create_user(client, external_id="delete-user")
    payload = {
        "title": "Task to delete",
        "description": "Delete me",
        "status": "new",
        "priority": 2,
        "source": "web",
    }

    create_response = client.post("/tasks", json=payload, headers={"X-User-Key": user["user_key"]})
    task_id = create_response.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 204

    get_response = client.get(f"/tasks/{task_id}", headers={"X-User-Key": user["user_key"]})
    assert get_response.status_code == 404


def test_create_task_requires_user_key(client):
    payload = {
        "title": "No key",
        "description": "Should fail",
        "status": "new",
        "priority": 1,
        "source": "web",
    }

    response = client.post("/tasks", json=payload)

    assert response.status_code == 422


def test_create_task_without_title(client):
    user = create_user(client, external_id="missing-title")
    payload = {
        "description": "No title",
        "status": "new",
        "priority": 1,
        "source": "web",
    }

    response = client.post("/tasks", json=payload, headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 422


def test_create_task_with_invalid_priority(client):
    user = create_user(client, external_id="bad-priority")
    payload = {
        "title": "Bad priority",
        "description": "Invalid priority",
        "status": "new",
        "priority": 10,
        "source": "web",
    }

    response = client.post("/tasks", json=payload, headers={"X-User-Key": user["user_key"]})

    assert response.status_code == 422


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mark_task_done_service(db_session):
    user = user_service.ensure_user_for_identity(
        db_session,
        provider="telegram",
        external_id="service-user",
        name="Service User",
    )
    task = task_service.create_task(
        db_session,
        user.id,
        TaskCreate(
            title="Finish backend",
            description="Prepare shared service layer",
            status="new",
            priority=2,
            source="telegram",
        ),
    )

    updated_task = task_service.mark_task_done(db_session, user.id, task.id)

    assert updated_task is not None
    assert updated_task.status == "done"

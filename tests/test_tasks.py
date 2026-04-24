def test_create_task(client):
    payload = {
        "title": "Learn pytest",
        "description": "Write API tests",
        "status": "new",
        "priority": 1
    }

    response = client.post("/tasks", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert isinstance(data["id"], int)

    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["status"] == payload["status"]
    assert data["priority"] == payload["priority"]


def test_get_tasks(client):
    payload = {
        "title": "Task 1",
        "description": "First task",
        "status": "new",
        "priority": 2
    }

    client.post("/tasks", json=payload)

    response = client.get("/tasks")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == payload["title"]


def test_get_task_by_id(client):
    payload = {
        "title": "Find me",
        "description": "Task by id",
        "status": "new",
        "priority": 3
    }

    create_response = client.post("/tasks", json=payload)
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == payload["title"]


def test_get_non_existing_task(client):
    response = client.get("/tasks/9999")

    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Task not found"

def test_update_task(client):
    create_payload = {
        "title": "Old title",
        "description": "Old description",
        "status": "new",
        "priority": 1
    }

    create_response = client.post("/tasks", json=create_payload)
    task_id = create_response.json()["id"]

    update_payload = {
        "title": "Updated title",
        "description": "Updated description",
        "status": "in_progress",
        "priority": 3
    }

    response = client.put(f"/tasks/{task_id}", json=update_payload)

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == update_payload["title"]
    assert data["description"] == update_payload["description"]
    assert data["status"] == update_payload["status"]
    assert data["priority"] == update_payload["priority"]

def test_delete_task(client):
    payload = {
        "title": "Task to delete",
        "description": "Delete me",
        "status": "new",
        "priority": 2
    }

    create_response = client.post("/tasks", json=payload)
    task_id = create_response.json()["id"]

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204

    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404

def test_create_task_without_title(client):
    payload = {
        "description": "No title",
        "status": "new",
        "priority": 1
    }

    response = client.post("/tasks", json=payload)

    assert response.status_code == 422

def test_create_task_with_invalid_priority(client):
    payload = {
        "title": "Bad priority",
        "description": "Invalid priority",
        "status": "new",
        "priority": 10
    }

    response = client.post("/tasks", json=payload)

    assert response.status_code == 422


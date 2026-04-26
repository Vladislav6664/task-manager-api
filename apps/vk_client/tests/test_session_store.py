from pathlib import Path

from apps.vk_client.app.session_store import VkSessionStore


def test_session_store_update_and_load(tmp_path: Path):
    store = VkSessionStore(str(tmp_path / "session.json"))

    store.update(vk_id="10001", user_key="TM-TEST")

    assert store.load() == {
        "vk_id": "10001",
        "user_key": "TM-TEST",
    }


def test_session_store_clear(tmp_path: Path):
    store = VkSessionStore(str(tmp_path / "session.json"))
    store.save({"vk_id": "10001"})

    store.clear()

    assert store.load() == {}

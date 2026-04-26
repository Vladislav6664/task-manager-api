import os

from apps.shared.env import load_env_file


load_env_file()


class Settings:
    backend_api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
    vk_external_id = os.getenv("VK_EXTERNAL_ID", "")
    session_path = os.getenv("VK_CLIENT_SESSION_PATH", ".vk_client_session.json")


settings = Settings()

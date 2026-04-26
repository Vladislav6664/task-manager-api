import os

from apps.shared.env import load_env_file


load_env_file()


class Settings:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    backend_api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")


settings = Settings()

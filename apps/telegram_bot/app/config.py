import os


class Settings:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    backend_api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")


settings = Settings()

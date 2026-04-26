import os


class Settings:
    backend_api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")


settings = Settings()

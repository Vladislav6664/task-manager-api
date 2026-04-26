import os


class Settings:
    app_name = "Task Manager API"
    cors_origins = os.getenv("TASK_MANAGER_CORS_ORIGINS", "*")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

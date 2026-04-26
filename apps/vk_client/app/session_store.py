import json
from pathlib import Path


class VkSessionStore:
    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict) -> None:
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def update(self, **kwargs) -> dict:
        data = self.load()
        data.update({key: value for key, value in kwargs.items() if value is not None})
        self.save(data)
        return data

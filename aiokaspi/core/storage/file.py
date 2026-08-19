from pathlib import Path

import tomli
import tomli_w

from aiokaspi.core.schemas import (
    Entity,
)
from aiokaspi.core.storage.base import BaseStorage


class FileStorage(BaseStorage):
    def __init__(self, path: str = "config.toml"):
        if not path.endswith(".toml"):
            raise ValueError("Unsupported file type, use .toml")
        self.path = Path(path)

    def get(self, entity: Entity) -> dict | None:
        try:
            with open(file=self.path, mode="rb") as f:
                storage: dict = tomli.load(f)
        except FileNotFoundError:
            return None
        if entity not in storage:
            return None
        return storage[entity]

    def save(self, entity: Entity, data: dict) -> None:
        path = Path(self.path)
        storage_data: dict = {}
        if path.exists():
            with open(file=path, mode="rb") as f:
                storage_data: dict = tomli.load(f)
        if entity == Entity.extra:
            extra: dict | None = self.get(entity=Entity.extra)
            if extra is not None:
                extra |= data
            else:
                extra: dict = data
            storage_data[entity.value] = extra
        else:
            storage_data[entity.value] = data

        with open(file=path, mode="wb") as f:
            tomli_w.dump(storage_data, f)

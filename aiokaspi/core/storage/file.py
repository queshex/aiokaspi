from dataclasses import asdict
from pathlib import Path
from typing import overload

import tomli
import tomli_w

from aiokaspi.core.schemas import (
    ENTITY_MAP,
    DeviceSchema,
    Entity,
    KeysSchema,
    SessionSchema,
)
from aiokaspi.core.storage.base import BaseStorage


class FileStorage(BaseStorage):
    def __init__(self, path: str = "config.toml"):
        if not path.endswith(".toml"):
            raise ValueError("Unsupported file type, use .toml")
        self.path = Path(path)

    @overload
    def get(self, entity: Entity.device) -> DeviceSchema: ...
    @overload
    def get(self, entity: Entity.keys) -> KeysSchema: ...
    @overload
    def get(self, entity: Entity.session) -> SessionSchema: ...

    def get(self, entity: Entity) -> SessionSchema | DeviceSchema | KeysSchema | None:
        try:
            with open(self.path, "rb") as f:
                storage = tomli.load(f)
        except FileNotFoundError:
            return None
        # TODO: Checking TOML format, otherwise raise an exception
        if entity not in storage:
            return None
        cls = ENTITY_MAP[entity]
        return cls(**storage[entity])

    @overload
    def save(self, entity: Entity.device, data: DeviceSchema) -> None: ...
    @overload
    def save(self, entity: Entity.keys, data: KeysSchema) -> None: ...
    @overload
    def save(self, entity: Entity.session, data: SessionSchema) -> None: ...

    def save(
        self, entity: Entity, data: SessionSchema | DeviceSchema | KeysSchema
    ) -> None:
        expected_type = ENTITY_MAP[entity]
        if not isinstance(data, expected_type):
            raise TypeError(
                f"Invalid data type for {entity.value}: expected {expected_type.__name__}, got {type(data).__name__}"
            )
        path = Path(self.path)
        storage_data = {}
        if path.exists():
            with open(path, "rb") as f:
                storage_data = tomli.load(f)

        storage_data[entity.value] = asdict(data)

        with open(path, "wb") as f:
            tomli_w.dump(storage_data, f)

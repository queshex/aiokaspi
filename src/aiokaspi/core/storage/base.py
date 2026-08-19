from typing import Protocol

from aiokaspi.core.schemas import Entity


class BaseStorage(Protocol):
    def get(self, entity: Entity) -> dict | None: ...

    def save(
        self,
        entity: Entity,
        data: dict,
    ) -> None: ...

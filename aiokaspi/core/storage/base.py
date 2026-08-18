from typing import Protocol, overload

from aiokaspi.core.schemas import DeviceSchema, Entity, KeysSchema, SessionSchema


class BaseStorage(Protocol):
    @overload
    def get(self, entity: Entity.device) -> DeviceSchema: ...
    @overload
    def get(self, entity: Entity.keys) -> KeysSchema: ...
    @overload
    def get(self, entity: Entity.session) -> SessionSchema: ...

    def get(
        self, entity: Entity
    ) -> SessionSchema | DeviceSchema | KeysSchema | None: ...

    @overload
    def save(self, entity: Entity.device, data: DeviceSchema) -> None: ...
    @overload
    def save(self, entity: Entity.keys, data: KeysSchema) -> None: ...
    @overload
    def save(self, entity: Entity.session, data: SessionSchema) -> None: ...

    def save(
        self, entity: Entity, data: SessionSchema | DeviceSchema | KeysSchema
    ) -> None: ...

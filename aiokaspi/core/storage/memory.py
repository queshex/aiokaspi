# from aiokaspi.core.schemas import (
#     BaseStorage,
#     Entity,
#     ENTITY_MAP,
#     SessionSchema,
#     DeviceSchema,
#     KeysSchema
# )
#
#
#
# class MemoryStorage(BaseStorage):
#     def __init__(self):
#         self.storage: dict[Entity, SessionSchema | DeviceSchema  | KeysSchema]] = {}
#
#     def get(self, entity: Entity) -> SessionSchema | DeviceSchema | KeysSchema]:
#         record: SessionSchema | DeviceSchema | KeysSchema | None = self.storage.get(entity)
#         if record is None:
#             raise KeyError(f"The storage does not have {entity} block")
#         return record
#
#     def save(self, entity: Entity, data: SessionSchema | DeviceSchema | KeysSchema) -> None:
#         self.storage[entity] = data

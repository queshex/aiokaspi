from typing import TYPE_CHECKING

from aiokaspi.core.keys import Keys as KeysGenerator
from aiokaspi.core.schemas import (
    Config,
    DeviceSchema,
    Entity,
    KeysSchema,
    SessionSchema,
)

if TYPE_CHECKING:
    from aiokaspi.core.storage import BaseStorage


class ConfigManager:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    @property
    def has_session(self) -> bool:
        return bool(self.storage.get(entity=Entity.session))

    def get_lazy_config(self) -> Config:
        device: DeviceSchema | None = self.storage.get(Entity.device)
        if device is None:
            device_id: str = KeysGenerator.generate_upper_uuid()
            install_id: str = KeysGenerator.generate_upper_uuid()
            pin_hash: str = KeysGenerator.generate_pin_hash()
            device: DeviceSchema = DeviceSchema(
                device_id=device_id, install_id=install_id, pin_hash=pin_hash
            )
            self.storage.save(entity=Entity.device, data=device)

        keys: KeysSchema | None = self.storage.get(Entity.keys)
        if keys is None:
            public_key, private_key = KeysGenerator.generate_keypair_base64()
            keys: KeysSchema = KeysSchema(
                public_key=public_key, private_key=private_key
            )
            self.storage.save(entity=Entity.keys, data=keys)

        session: SessionSchema | None = self.storage.get(Entity.session)

        pk: str = KeysGenerator.get_pk(keys.public_key)
        pk_tag: str = KeysGenerator.get_pk_tag(keys.public_key)
        return Config.from_sources(
            pk=pk, pk_tag=pk_tag, device=device, keys=keys, session=session
        )

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


@dataclass
class Config:
    public_key: str
    private_key: str
    pk: str
    pk_tag: str
    device_id: str
    install_id: str
    pin_hash: str
    x509: str | None = None
    token_sn: str | None = None
    user_id_hash: str | None = None

    @classmethod
    def from_sources(
        cls,
        pk: str,
        pk_tag: str,
        device: DeviceSchema,
        keys: KeysSchema,
        session: SessionSchema | None = None,
    ) -> Config:
        data = {
            "pk": pk,
            "pk_tag": pk_tag,
            **asdict(device),
            **asdict(keys),
        }
        if session is not None:
            data |= asdict(session)
        return cls(**data)


class Entity(str, Enum):
    device = "device"
    keys = "keys"
    session = "session"


@dataclass
class SessionSchema:
    x509: str
    token_sn: str
    user_id_hash: str


@dataclass
class DeviceSchema:
    device_id: str
    install_id: str
    pin_hash: str


@dataclass
class KeysSchema:
    public_key: str
    private_key: str


ENTITY_MAP = {
    Entity.device: DeviceSchema,
    Entity.keys: KeysSchema,
    Entity.session: SessionSchema,
}

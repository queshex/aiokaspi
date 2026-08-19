from __future__ import annotations

from dataclasses import dataclass, field
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
    extras: dict = field(default_factory=dict)

    @classmethod
    def from_sources(
        cls,
        pk: str,
        pk_tag: str,
        device: dict,
        keys: dict,
        session: dict | None = None,
        extra: dict | None = None,
    ) -> Config:
        data = {
            "pk": pk,
            "pk_tag": pk_tag,
            **device,
            **keys,
        }
        if session:
            data |= session
        if extra:
            data["extras"] = extra
        return cls(**data)


class Entity(str, Enum):
    device = "device"
    keys = "keys"
    session = "session"
    extra = "extra"


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

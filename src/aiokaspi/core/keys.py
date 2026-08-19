from __future__ import annotations

import base64
import hashlib
import hmac
import time
import json
import uuid
from random import randint
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


class Keys:
    @staticmethod
    def generate_keypair_base64() -> tuple[str, str]:
        private_key: ec.EllipticCurvePrivateKey = ec.generate_private_key(
            ec.SECP256R1()
        )
        public_key: ec.EllipticCurvePublicKey = private_key.public_key()

        private_key: str = base64.b64encode(
            private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        ).decode("utf-8")

        public_key: str = base64.b64encode(
            public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode("utf-8")

        return public_key, private_key

    @staticmethod
    def get_pk(public_key: str) -> str:
        pub_key_der = base64.b64decode(public_key)
        uncompressed_point = pub_key_der[-65:]
        return base64.b64encode(uncompressed_point).decode("utf-8")

    @staticmethod
    def get_pk_tag(public_key: str) -> str:
        pk = Keys.get_pk(public_key)
        return hashlib.md5(pk.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_pin_hash(pin: str = str(randint(1000, 9999))) -> str:
        return hashlib.sha256(pin.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_upper_uuid() -> str:
        return str(uuid.uuid4()).upper()

    @staticmethod
    def sign_data(data: str, private_key: str) -> str:
        private_bytes = base64.b64decode(private_key)
        pk = serialization.load_der_private_key(private_bytes, password=None)
        if isinstance(data, str):
            data = data.encode("utf-8")
        signature = pk.sign(data, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    def compute_x_su(url: str) -> str:
        return hashlib.md5(url.lower().encode("utf-8")).hexdigest()

    @staticmethod
    def compute_x_sign(
        url: str, headers: dict, x_sh: str, private_key: str, body=None
    ) -> str:
        lines = []
        formatted_x_shs: list[str] = x_sh.split(",")
        for sh in formatted_x_shs:
            if sh == "url":
                lines.append(f"url:{url}")
            else:
                lines.append(f"{sh.lower()}:{headers[sh]}")
        string_to_sign: str = "\n".join(lines)
        if body:
            string_to_sign += "\n" + json.dumps(body.asdict_with_aliases())
        hash_obj = hashlib.sha256(string_to_sign.encode("utf-8")).digest()
        return Keys.sign_data(hash_obj, private_key)

    @staticmethod
    def token_sn_mac(token_sn: str, secret: str | bytes | None = None) -> str:
        return compute_token_sn_mac(token_sn=token_sn, secret=secret)

    @staticmethod
    def complete_ecdh(x509: str, private_key: str):
        private_key = serialization.load_der_private_key(
            base64.b64decode(private_key), password=None
        )
        if not isinstance(private_key, ec.EllipticCurvePrivateKey):
            raise ValueError("Private key is not an EC private key")
        server_public_key = serialization.load_der_public_key(base64.b64decode(x509))
        if not isinstance(server_public_key, ec.EllipticCurvePublicKey):
            raise ValueError("Server key is not an EC public key")
        shared_secret = private_key.exchange(ec.ECDH(), server_public_key)

        return shared_secret


def compute_token_sn_mac(token_sn: str, secret: str | bytes | None = None) -> str:
    """Вычисляет 6-значный время-зависимый MAC для серийного номера токена.

    Args:
        token_sn: Серийный номер токена. Если пусто — используется '00000000'.
        secret: Секретный ключ для HMAC. Если falsy — возвращается MAC-заглушка.

    Returns:
        Строка из 6 цифр (с ведущими нулями при необходимости).
    """
    default_mac = "000000"
    if not secret:
        return default_mac

    # Суффикс OCRA (RFC 6287): версия алгоритма + крипто-функция + формат данных.
    # Смешивается в HMAC, чтобы MAC был привязан к конкретному набору параметров
    # (алгоритм, длина хэша, формат challenge/времени) и не мог быть подменён
    # значением, посчитанным по другой схеме.
    token_suite = b"OCRA-1:HOTP-SHA256-6:QH64-T1M"

    time_step_seconds = 30
    q_hex_length = 256  # длина hex-строки серийного номера после паддинга (128 байт)
    t_hex_length = 16  # длина hex-строки временного шага после паддинга (8 байт)
    mac_digits = 6

    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret

    time_step = int(time.time() * 1000) // (time_step_seconds * 1000)
    time_hex = format(time_step, "x")

    q_hex = (token_sn or "00000000").encode("utf-8").hex()[:64]
    q_hex_padded = q_hex.ljust(q_hex_length, "0")
    t_hex_padded = time_hex.rjust(t_hex_length, "0")

    data = (
        token_suite
        + b"\x00"
        + bytes.fromhex(q_hex_padded)
        + bytes.fromhex(t_hex_padded)
    )

    digest = hmac.new(secret_bytes, data, hashlib.sha256).digest()
    return _rfc4226_truncate(digest, mac_digits)


def _rfc4226_truncate(digest: bytes, digits: int) -> str:
    """Применяет динамическое усечение HMAC-дайджеста по RFC 4226."""
    offset = digest[-1] & 0x0F
    bin_code = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    return str(bin_code % (10**digits)).zfill(digits)

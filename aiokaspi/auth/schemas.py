from __future__ import annotations

import base64, json, re, uuid
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Optional
from urllib.parse import urlencode


class Step(str, Enum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    FINISH = "finish"

class ErrorCode(str, Enum):
    INVALID_PHONE_NUMBER = "UserPhoneNumberDoesNotBelongToAnyOperator"
    INVALID_OTP = "OtpCodeIsWrong"
    TEMPORARY_BLOCKED = "TemporaryBlocked"
    BAD_REQUEST = "BadIncomingRequest"
    ENTER_OTP_ATTEMPTS_EXCEEDED = "EnterOtpAttemptsExceeded"
    CONTEXT_NOT_FOUND = "ContextNotFound"
    PASSWORD_IS_EMPTY = "PasswordIsEmpty"
    PASSWORD_ATTEMPTS_EXCEEDED = "PasswordAttemptsExceeded"
    OLD_VERSION_TO_UPDATE = "OldVersionToUpdate"
    KASPI_PAY_CHECK_SECURITY_FAILED = "KaspiPayCheckSecurityFailed"

class SN(str, Enum):
    ENTER_PHONE_NUMBER = "EnterPhoneNumber"
    VIEW_ENTER_OTP = "ViewEnterOtp"
    MOBILE_DEVICE_REGISTRATION = "MobileDeviceRegistration"
    VIEW_ENTER_LOGIN_PASSWORD = "ViewEnterLoginPassword"
    VIEW_KASPI_ID_TAKE_PHOTO = "ViewKaspiIdTakePhoto"
    WEB_ORG_REGISTRATION = "WebOrgRegistration"
    SHOW_ALERT_ON_FIRST_VIEW = "ShowAlertOnFirstView"
    SYSTEM_ERROR = "SystemError"


def _alias(name: str) -> dict:
    """Shortcut to create metadata dict with an alias."""
    return {"alias": name}


@dataclass(slots=True)
class BaseSchema:
    """Base for all dataclass-based schemas.

    Provides alias-aware serialization via `asdict_with_aliases()`
    and alias-aware construction via `from_dict()`.
    """

    @classmethod
    def from_dict(cls, data: dict) -> BaseSchema:
        """Create an instance from a dict with alias keys (e.g. API response JSON)."""
        alias_to_field: dict[str, str] = {}
        for f in fields(cls):
            alias = f.metadata.get("alias", f.name)
            alias_to_field[alias] = f.name
        kwargs = {}
        for key, value in data.items():
            field_name = alias_to_field.get(key)
            if field_name is not None:
                kwargs[field_name] = value
        return cls(**kwargs)

    def asdict_with_aliases(self) -> dict:
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            key = f.metadata.get("alias", f.name)
            if isinstance(value, BaseSchema):
                value = value.asdict_with_aliases()
            elif isinstance(value, list):
                value = [
                    item.asdict_with_aliases() if isinstance(item, BaseSchema) else item
                    for item in value
                ]
            elif isinstance(value, Enum):
                value = value.value
            result[key] = value
        return result


# ─────────────────────────── Meta ───────────────────────────

@dataclass(slots=True)
class Meta(BaseSchema):
    p_id: str = field(metadata=_alias("pId"))
    sn: SN = field(metadata=_alias("sn"))


# ─────────────────────── Step 1 (init) ──────────────────────

@dataclass(slots=True)
class FirstStepRequestData(BaseSchema):
    device_id: str = field(metadata=_alias("deviceId"))
    install_id: str = field(metadata=_alias("installId"))

    app_build: str = field(default="1099", metadata=_alias("appBuild"))
    app_version: str = field(default="4.110.1", metadata=_alias("appVersion"))
    auth: str = field(default="2", metadata=_alias("auth"))
    device_brand: str = field(default="Apple", metadata=_alias("deviceBrand"))
    device_model: str = field(default="iPhone17,3", metadata=_alias("deviceModel"))
    front_camera_available: str = field(default="true", metadata=_alias("frontCameraAvailable"))
    no_pass: str = field(default="0", metadata=_alias("noPass"))
    pc: str = field(default="KPEntrance", metadata=_alias("pc"))
    platform_type: str = field(default="IOS", metadata=_alias("platformType"))
    platform_version: str = field(default="18.5", metadata=_alias("platformVersion"))
    sf: str = field(default="registration", metadata=_alias("sf"))

    def __post_init__(self) -> None:
        if not self.app_build.isdigit():
            raise ValueError(f"appBuild must be a number: {self.app_build}")
        if not re.match(r"^\d+\.\d+\.\d+$", self.app_version):
            raise ValueError(f"appVersion must be in format X.Y.Z: {self.app_version}")
        if not self.auth.isdigit() or len(self.auth) != 1:
            raise ValueError(f"auth must be a single digit: {self.auth}")
        if self.front_camera_available.lower() not in ("true", "false"):
            raise ValueError(f"frontCameraAvailable must be true or false: {self.front_camera_available}")
        if not self.no_pass.isdigit() or len(self.no_pass) != 1:
            raise ValueError(f"noPass must be a single digit: {self.no_pass}")

    @property
    def referer(self) -> str:
        query: str = urlencode(self.asdict_with_aliases())
        return f"https://entrance-pay.kaspi.kz/process/entrance/?{query}"


@dataclass(slots=True, kw_only=True)
class FirstStepRequest(BaseSchema):
    dt: dict = field(default_factory=dict, metadata=_alias("data"))
    data: FirstStepRequestData = field(metadata=_alias("Data"))
    act_type: str = field(default="Success", metadata=_alias("actType"))


# ─────────────────────── Step 2 (OTP) ──────────────────────

@dataclass(slots=True)
class SecondStepRequestData(BaseSchema):
    phone_number: str = field(metadata=_alias("phoneNumber"))

    def __post_init__(self) -> None:
        n = self.phone_number
        if n.startswith("8") and len(n) == 11:
            n = n[1:]
        elif n.startswith("77") and len(n) == 11:
            n = n[1:]
        elif n.startswith("+77") and len(n) == 12:
            n = n[2:]

        if not n.isdigit():
            raise ValueError(f"phone_number must be a number: {self.phone_number}")
        if not n.startswith("7"):
            raise ValueError(f"phone_number must start with 7: {self.phone_number}")
        if len(n) != 10:
            raise ValueError(f"phone_number must be 10 digits long: {self.phone_number}")


@dataclass(slots=True)
class SecondStepRequest(BaseSchema):
    meta: Meta = field(metadata=_alias("meta"))
    data: dict = field(default_factory=dict, metadata=_alias("data"))
    act_type: str = field(default="Success", metadata=_alias("actType"))

    @property
    def referer(self) -> str:
        return f"https://entrance-pay.kaspi.kz/process/universal-enter-phone-number?pId={self.meta.p_id}&firstPage=KPUniversalEnterPhoneNumber"


# ──────────────────── Step 3 (confirm OTP) ──────────────────

@dataclass(slots=True)
class ThirdStepRequestData(BaseSchema):
    user_otp: str = field(metadata=_alias("userOtp"))
    input_type: str = field(default="auto", metadata=_alias("inputType"))

    def __post_init__(self) -> None:
        if self.input_type not in ("manual", "auto"):
            raise ValueError(f"inputType must be 'manual' or 'auto': {self.input_type}")
        if not self.user_otp.isdigit():
            raise ValueError("User OTP must contain only digits")
        if len(self.user_otp) != 4:
            raise ValueError("User OTP must be 4 digits long")


@dataclass(slots=True)
class ThirdStepRequest(BaseSchema):
    meta: Meta = field(metadata=_alias("meta"))
    data: ThirdStepRequestData = field(metadata=_alias("data"))
    act_type: str = field(default="Success", metadata=_alias("actType"))

    @property
    def referer(self) -> str:
        return f"https://entrance-pay.kaspi.kz/process/universal-enter-phone-number?pId={self.meta.p_id}&firstPage=KPUniversalEnterPhoneNumber"


# ──────────────────────── Finish ────────────────────────────

@dataclass(slots=True)
class Guard(BaseSchema):
    pin_hash: str = field(metadata=_alias("pinHash"))
    x509: str = field(metadata=_alias("x509"))

@dataclass(slots=True)
class Auth(BaseSchema):
    value: str = field(default="", metadata=_alias("value"))
    type: str = field(default="pincode", metadata=_alias("type"))

@dataclass(slots=True)
class DataToSign(BaseSchema):
    auth: list[Auth] = field(metadata=_alias("auth"))
    time: str = field(metadata=_alias("time"))
    install_id: str = field(metadata=_alias("installId"))
    user_id_hash: str = field(default="", metadata=_alias("userIdHash"))

    def base64(self) -> str:
        return base64.b64encode(
            json.dumps(self.asdict_with_aliases()).encode("utf-8")
        ).decode("utf-8")

@dataclass(slots=True)
class Signed(BaseSchema):
    data: str = field(metadata=_alias("data"))
    sign: str = field(metadata=_alias("sign"))

@dataclass(slots=True)
class FinishRequest(BaseSchema):
    guard: Guard = field(metadata=_alias("guard"))
    process_id: str = field(metadata=_alias("processId"))
    signed: Signed = field(metadata=_alias("signed"))
    act_type: str = field(default="Success", metadata=_alias("actType"))

@dataclass(slots=True)
class FinishResponse(BaseSchema):
    token_sn: str = field(metadata=_alias("tokenSN"))
    x509: str = field(metadata=_alias("x509"))
    user_id_hash: str = field(metadata=_alias("userIdHash"))


# ──────────────────────── Logout ────────────────────────────

@dataclass(slots=True)
class LogoutRequest(BaseSchema):
    device_id: str = field(metadata=_alias("DeviceId"))
    token_sn: str = field(metadata=_alias("TokenSn"))


# ──────────────────────── Cookies / Headers ─────────────────

@dataclass(slots=True)
class StepCookie(BaseSchema):
    device_id: str = field(metadata=_alias("deviceId"))
    install_id: str = field(metadata=_alias("installId"))
    pk: str = field(metadata=_alias("pk"))
    pk_tag: str = field(metadata=_alias("pkTag"))

    is_mobile_app: str = field(default="true", metadata=_alias("is_mobile_app"))
    locale: str = field(default="ru-RU", metadata=_alias("locale"))
    ma_bld: str = field(default="1099", metadata=_alias("ma_bld"))
    ma_platform_type: str = field(default="IOS", metadata=_alias("ma_platform_type"))
    ma_platform_ver: str = field(default="26.5", metadata=_alias("ma_platform_ver"))
    ma_ver: str = field(default="4.110.1", metadata=_alias("ma_ver"))
    new_pay_connection: str = field(default="true", metadata=_alias("new-pay-connection"))
    xs: str = field(default="R:0|E:0|RH:0|N:0|GS:0", metadata=_alias("xs"))

    user_token: Optional[str] = field(default=None, metadata=_alias("user_token"))

    def to_cookie_string(self) -> str:
        data = self.asdict_with_aliases()
        return "; ".join(f"{k}={v}" for k, v in data.items() if v is not None)


@dataclass(slots=True)
class StepHeaders(BaseSchema):
    referer: str = field(metadata=_alias("Referer"))
    cookie: StepCookie = field(metadata=_alias("Cookie"))

    accept: str = field(default="application/json, text/plain, */*", metadata=_alias("Accept"))
    content_type: str = field(default="application/json", metadata=_alias("Content-Type"))
    accept_language: str = field(default="ru", metadata=_alias("Accept-Language"))
    accept_encoding: str = field(default="gzip, deflate, br", metadata=_alias("Accept-Encoding"))
    origin: str = field(default="https://entrance-pay.kaspi.kz", metadata=_alias("Origin"))
    sec_fetch_site: str = field(default="same-origin", metadata=_alias("Sec-Fetch-Site"))
    sec_fetch_mode: str = field(default="cors", metadata=_alias("Sec-Fetch-Mode"))
    sec_fetch_dest: str = field(default="empty", metadata=_alias("Sec-Fetch-Dest"))
    user_agent: str = field(
        default="Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        metadata=_alias("User-Agent"),
    )

    def asdict_with_aliases(self) -> dict:
        """Override: Cookie must be serialised as a string, not a nested dict."""
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            key = f.metadata.get("alias", f.name)
            if isinstance(value, StepCookie):
                value = value.to_cookie_string()
            elif isinstance(value, BaseSchema):
                value = value.asdict_with_aliases()
            elif isinstance(value, Enum):
                value = value.value
            result[key] = value
        return result


@dataclass(slots=True)
class PreFinishHeaders(BaseSchema):
    x_time: str = field(metadata=_alias("x-time"))
    x_pktag: str = field(metadata=_alias("x-pktag"))
    x_su: str = field(metadata=_alias("x-su"))

    x_call: str = field(default="notConnected", metadata=_alias("x-call"))
    user_agent: str = field(default="Kaspi%20Pay/1104 CFNetwork/3860.600.12 Darwin/25.5.0", metadata=_alias("user-agent"))
    x_platform_type: str = field(default="IOS", metadata=_alias("x-platform-type"))
    priority: str = field(default="u=3, i", metadata=_alias("priority"))
    x_net_type: str = field(default="WIFI/ETHERNET", metadata=_alias("x-net-type"))
    x_emulator: str = field(default="0", metadata=_alias("x-emulator"))
    accept_language: str = field(default="ru", metadata=_alias("accept-language"))
    x_locale: str = field(default="ru-RU", metadata=_alias("x-locale"))
    x_sv: str = field(default="2", metadata=_alias("x-sv"))
    x_request_id: str = field(default_factory=lambda: str(uuid.uuid4()).upper(), metadata=_alias("x-request-id"))
    x_time_zone: str = field(default="GMT+05:00", metadata=_alias("x-time-zone"))
    content_type: str = field(default="application/json", metadata=_alias("content-type"))
    accept: str = field(default="*/*", metadata=_alias("accept"))
    accept_encoding: str = field(default="gzip, deflate, br", metadata=_alias("accept-encoding"))
    x_sh: str = field(default="url,X-Platform-Type,X-Time,X-Locale,X-Emulator,X-Call,X-Net-Type,X-SV,X-Time-Zone", metadata=_alias("x-sh"))


@dataclass(slots=True)
class FinishHeaders(BaseSchema):
    """Finish headers = PreFinishHeaders fields + x-sign.
    
    Use `FinishHeaders.from_pre(pre_headers, x_sign)` to construct.
    """
    x_time: str = field(metadata=_alias("x-time"))
    x_pktag: str = field(metadata=_alias("x-pktag"))
    x_su: str = field(metadata=_alias("x-su"))
    x_sign: str = field(metadata=_alias("x-sign"))

    x_call: str = field(default="notConnected", metadata=_alias("x-call"))
    user_agent: str = field(default="Kaspi%20Pay/1104 CFNetwork/3860.600.12 Darwin/25.5.0", metadata=_alias("user-agent"))
    x_platform_type: str = field(default="IOS", metadata=_alias("x-platform-type"))
    priority: str = field(default="u=3, i", metadata=_alias("priority"))
    x_net_type: str = field(default="WIFI/ETHERNET", metadata=_alias("x-net-type"))
    x_emulator: str = field(default="0", metadata=_alias("x-emulator"))
    accept_language: str = field(default="ru", metadata=_alias("accept-language"))
    x_locale: str = field(default="ru-RU", metadata=_alias("x-locale"))
    x_sv: str = field(default="2", metadata=_alias("x-sv"))
    x_request_id: str = field(default_factory=lambda: str(uuid.uuid4()).upper(), metadata=_alias("x-request-id"))
    x_time_zone: str = field(default="GMT+05:00", metadata=_alias("x-time-zone"))
    content_type: str = field(default="application/json", metadata=_alias("content-type"))
    accept: str = field(default="*/*", metadata=_alias("accept"))
    accept_encoding: str = field(default="gzip, deflate, br", metadata=_alias("accept-encoding"))
    x_sh: str = field(default="url,X-Platform-Type,X-Time,X-Locale,X-Emulator,X-Call,X-Net-Type,X-SV,X-Time-Zone", metadata=_alias("x-sh"))

    @classmethod
    def from_pre(cls, pre: PreFinishHeaders, x_sign: str) -> FinishHeaders:
        """Create FinishHeaders from existing PreFinishHeaders + computed x-sign."""
        return cls(
            x_time=pre.x_time,
            x_pktag=pre.x_pktag,
            x_su=pre.x_su,
            x_sign=x_sign,
            x_call=pre.x_call,
            user_agent=pre.user_agent,
            x_platform_type=pre.x_platform_type,
            priority=pre.priority,
            x_net_type=pre.x_net_type,
            x_emulator=pre.x_emulator,
            accept_language=pre.accept_language,
            x_locale=pre.x_locale,
            x_sv=pre.x_sv,
            x_request_id=pre.x_request_id,
            x_time_zone=pre.x_time_zone,
            content_type=pre.content_type,
            accept=pre.accept,
            accept_encoding=pre.accept_encoding,
            x_sh=pre.x_sh,
        )


@dataclass(slots=True)
class LogoutHeaders(BaseSchema):
    #TODO: Перепроверить default поля

    x_kb_client_ip: str = field(metadata=_alias("X-Kb-Client-Ip"))
    x_sign: str = field(metadata=_alias("X-Sign"))
    x_kb_token_sn_mac: str = field(metadata=_alias("X-Kb-TokenSnMac"))
    x_kb_token_sn: str = field(metadata=_alias("X-Kb-TokenSn"))

    x_time: str = field(default="2026-07-01T20:00:35.137+0500", metadata=_alias("X-Time"))
    x_pi: str = field(default="3777205", metadata=_alias("X-PI"))
    host: str = field(default="mtoken.kaspi.kz", metadata=_alias("Host"))
    x_locale: str = field(default="ru-RU", metadata=_alias("X-Locale"))
    accept: str = field(default="*/*", metadata=_alias("Accept"))
    x_sv: str = field(default="2", metadata=_alias("X-SV"))
    accept_language: str = field(default="ru", metadata=_alias("Accept-Language"))
    accept_encoding: str = field(default="gzip, deflate, br", metadata=_alias("Accept-Encoding"))
    content_type: str = field(default="application/json", metadata=_alias("Content-Type"))
    x_call: str = field(default="notConnected", metadata=_alias("X-Call"))
    user_agent: str = field(default="Kaspi%20Pay/1104 CFNetwork/3860.600.12 Darwin/25.5.0", metadata=_alias("User-Agent"))
    connection: str = field(default="keep-alive", metadata=_alias("Connection"))
    x_s: str = field(default="R:0|E:0|RH:0|N:0|GS:0", metadata=_alias("X-S"))
    x_sh: str = field(default="url,X-SV,X-Kb-Client-Ip,X-Time,X-Call,X-Locale,X-Kb-TokenSnMac,X-Kb-TokenSn,X-S,X-PI", metadata=_alias("X-SH"))
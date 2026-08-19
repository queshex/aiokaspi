from __future__ import annotations

import base64
import json
import re
import uuid
from dataclasses import dataclass, field, fields
from enum import Enum
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

    app_build: str = field(default="1113", metadata=_alias("appBuild"))
    app_version: str = field(default="4.110.1", metadata=_alias("appVersion"))
    auth: str = field(default="2", metadata=_alias("auth"))
    device_brand: str = field(default="Apple", metadata=_alias("deviceBrand"))
    device_model: str = field(default="iPhone17,3", metadata=_alias("deviceModel"))
    front_camera_available: str = field(
        default="true", metadata=_alias("frontCameraAvailable")
    )
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
            raise ValueError(
                f"frontCameraAvailable must be true or false: {self.front_camera_available}"
            )
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
        if n.startswith("8") and len(n) == 11 or n.startswith("77") and len(n) == 11:
            n = n[1:]
        elif n.startswith("+77") and len(n) == 12:
            n = n[2:]

        if not n.isdigit():
            raise ValueError(f"phone_number must be a number: {self.phone_number}")
        if not n.startswith("7"):
            raise ValueError(f"phone_number must start with 7: {self.phone_number}")
        if len(n) != 10:
            raise ValueError(
                f"phone_number must be 10 digits long: {self.phone_number}"
            )
        self.phone_number = n


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
    new_pay_connection: str = field(
        default="true", metadata=_alias("new-pay-connection")
    )
    xs: str = field(default="R:0|E:0|RH:0|N:0|GS:0", metadata=_alias("xs"))

    user_token: str | None = field(default=None, metadata=_alias("user_token"))

    def to_cookie_string(self) -> str:
        data = self.asdict_with_aliases()
        return "; ".join(f"{k}={v}" for k, v in data.items() if v is not None)


@dataclass(slots=True)
class StepHeaders(BaseSchema):
    referer: str = field(metadata=_alias("Referer"))
    cookie: StepCookie = field(metadata=_alias("Cookie"))

    accept: str = field(
        default="application/json, text/plain, */*", metadata=_alias("Accept")
    )
    content_type: str = field(
        default="application/json", metadata=_alias("Content-Type")
    )
    accept_language: str = field(default="ru", metadata=_alias("Accept-Language"))
    accept_encoding: str = field(
        default="gzip, deflate, br", metadata=_alias("Accept-Encoding")
    )
    origin: str = field(
        default="https://entrance-pay.kaspi.kz", metadata=_alias("Origin")
    )
    sec_fetch_site: str = field(
        default="same-origin", metadata=_alias("Sec-Fetch-Site")
    )
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
    user_agent: str = field(
        default="Kaspi%20Pay/1104 CFNetwork/3860.600.12 Darwin/25.5.0",
        metadata=_alias("user-agent"),
    )
    x_platform_type: str = field(default="IOS", metadata=_alias("x-platform-type"))
    priority: str = field(default="u=3, i", metadata=_alias("priority"))
    x_net_type: str = field(default="WIFI/ETHERNET", metadata=_alias("x-net-type"))
    x_emulator: str = field(default="0", metadata=_alias("x-emulator"))
    accept_language: str = field(default="ru", metadata=_alias("accept-language"))
    x_locale: str = field(default="ru-RU", metadata=_alias("x-locale"))
    x_sv: str = field(default="2", metadata=_alias("x-sv"))
    x_request_id: str = field(
        default_factory=lambda: str(uuid.uuid4()).upper(),
        metadata=_alias("x-request-id"),
    )
    x_time_zone: str = field(default="GMT+05:00", metadata=_alias("x-time-zone"))
    content_type: str = field(
        default="application/json", metadata=_alias("content-type")
    )
    accept: str = field(default="*/*", metadata=_alias("accept"))
    accept_encoding: str = field(
        default="gzip, deflate, br", metadata=_alias("accept-encoding")
    )
    x_sh: str = field(
        default="url,X-Platform-Type,X-Time,X-Locale,X-Emulator,X-Call,X-Net-Type,X-SV,X-Time-Zone",
        metadata=_alias("x-sh"),
    )


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
    user_agent: str = field(
        default="Kaspi%20Pay/1104 CFNetwork/3860.600.12 Darwin/25.5.0",
        metadata=_alias("user-agent"),
    )
    x_platform_type: str = field(default="IOS", metadata=_alias("x-platform-type"))
    priority: str = field(default="u=3, i", metadata=_alias("priority"))
    x_net_type: str = field(default="WIFI/ETHERNET", metadata=_alias("x-net-type"))
    x_emulator: str = field(default="0", metadata=_alias("x-emulator"))
    accept_language: str = field(default="ru", metadata=_alias("accept-language"))
    x_locale: str = field(default="ru-RU", metadata=_alias("x-locale"))
    x_sv: str = field(default="2", metadata=_alias("x-sv"))
    x_request_id: str = field(
        default_factory=lambda: str(uuid.uuid4()).upper(),
        metadata=_alias("x-request-id"),
    )
    x_time_zone: str = field(default="GMT+05:00", metadata=_alias("x-time-zone"))
    content_type: str = field(
        default="application/json", metadata=_alias("content-type")
    )
    accept: str = field(default="*/*", metadata=_alias("accept"))
    accept_encoding: str = field(
        default="gzip, deflate, br", metadata=_alias("accept-encoding")
    )
    x_sh: str = field(
        default="url,X-SV,X-Time-Zone,X-Emulator,X-Locale,X-Call,X-Time,X-Net-Type,X-Install-ID,X-Platform-Type",
        metadata=_alias("x-sh"),
    )

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
class PreContextHeaders(BaseSchema):
    x_time: str = field(metadata=_alias("X-Time"))
    x_pktag: str = field(metadata=_alias("X-PkTag"))
    x_su: str = field(metadata=_alias("X-SU"))
    x_kb_tokensn: str = field(metadata=_alias("X-Kb-TokenSn"))
    x_kb_client_ip: str = field(metadata=_alias("X-Kb-Client-Ip"))
    x_install_id: str = field(metadata=_alias("X-Install-ID"))
    x_kb_tokensnmac: str = field(metadata=_alias("X-Kb-TokenSnMac"))

    host: str = field(default="mtoken.kaspi.kz", metadata=_alias("Host"))
    accept_encoding: str = field(
        default="gzip, deflate, br", metadata=_alias("Accept-Encoding")
    )
    x_call: str = field(default="notConnected", metadata=_alias("X-Call"))
    user_agent: str = field(
        default="Kaspi%20Pay/1104 CFNetwork/3860.600.12 Darwin/25.5.0",
        metadata=_alias("User-Agent"),
    )
    x_app_bld: str = field(default="1113", metadata=_alias("X-App-Bld"))
    x_sh: str = field(
        default="url,X-Call,X-Kb-Client-Ip,X-Locale,X-Install-ID,X-Time,X-App-Ver,X-App-Bld,X-Kb-TokenSn,X-S,X-SV,X-Kb-TokenSnMac",
        metadata=_alias("X-SH"),
    )
    x_app_ver: str = field(default="4.114", metadata=_alias("X-App-Ver"))
    x_locale: str = field(default="ru-RU", metadata=_alias("X-Locale"))
    accept_language: str = field(default="ru", metadata=_alias("Accept-Language"))
    x_s: str = field(default="R:0|E:0|RH:0|N:0|GS:0", metadata=_alias("X-S"))
    x_sv: str = field(default="2", metadata=_alias("X-SV"))
    accept: str = field(default="*/*", metadata=_alias("accept"))


@dataclass(slots=True, kw_only=True)
class ContextHeaders(PreContextHeaders):
    x_sign: str = field(metadata=_alias("X-Sign"))

    @classmethod
    def from_pre(cls, pre: PreContextHeaders, x_sign: str) -> ContextHeaders:
        return cls(
            x_time=pre.x_time,
            x_pktag=pre.x_pktag,
            x_su=pre.x_su,
            x_kb_tokensn=pre.x_kb_tokensn,
            x_kb_client_ip=pre.x_kb_client_ip,
            x_install_id=pre.x_install_id,
            x_kb_tokensnmac=pre.x_kb_tokensnmac,
            host=pre.host,
            accept_encoding=pre.accept_encoding,
            x_call=pre.x_call,
            user_agent=pre.user_agent,
            x_app_bld=pre.x_app_bld,
            x_sh=pre.x_sh,
            x_app_ver=pre.x_app_ver,
            x_locale=pre.x_locale,
            accept_language=pre.accept_language,
            x_s=pre.x_s,
            x_sv=pre.x_sv,
            accept=pre.accept,
            x_sign=x_sign,
        )


@dataclass(slots=True)
class DeviceInformation(BaseSchema):
    device_id: str = field(metadata=_alias("DeviceId"))  # config sensetive
    install_id: str = field(metadata=_alias("InstallId"))  # config sensetive

    device_name: str = field(default="iPhone", metadata=_alias("DeviceName"))
    platform: str = field(default="iOS", metadata=_alias("Platform"))
    front_camera_available: bool = field(
        default=True, metadata=_alias("frontCameraAvailable")
    )
    product: str = field(default="Kaspi Pay", metadata=_alias("Product"))
    sdk_version: str = field(default="AOTP service", metadata=_alias("SdkVersion"))
    board: str = field(default="26.5.2", metadata=_alias("Board"))
    screen_width: str = field(default="320.0", metadata=_alias("ScreenWidth"))
    version_code: str = field(default="1113", metadata=_alias("VersionCode"))
    buildRelease: str = field(default="iOS 26.5.2", metadata=_alias("BuildRelease"))
    application_id: str = field(
        default="kz.kaspi.business", metadata=_alias("ApplicationId")
    )
    brand: str = field(default="Apple", metadata=_alias("Brand"))
    version_name: str = field(default="4.114", metadata=_alias("VersionName"))
    screeen_height: str = field(default="693.0", metadata=_alias("ScreenHeight"))
    model: str = field(default="iPhone15,4", metadata=_alias("Model"))


@dataclass(slots=True)
class ContextRequestData(BaseSchema):
    device_information: DeviceInformation = field(
        metadata=_alias("DeviceInformation")
    )  # TODO:
    organization_id: int = field(default=0, metadata=_alias("OrganizationId"))


#
# чевых проблемы в me() (org-context-otp):
#   ──────
#   ### 1. X-Kb-TokenSnMac — неправильный алгоритм
#
#   Твой код (keys.py:85-87):
#
#     def token_sn_mac(token_sn: str) -> str:
#         return str(zlib.crc32(token_sn.encode()) % 1000000)  # CRC32 — неправильно!
#
#   Рабочий референс (crypto.js:105-137 https://github.com/tapter-dev/kaspi-pos-automation/blob/main/src/crypto.js):
#
# �    // OCRA-1:HOTP-SHA256-6:QH64-T1M — HMAC-SHA256 с shared secret от ECDH
#     const computeTokenSnMac = (tokenSN, secret) => { ... }
#
#   Токен X-Kb-TokenSnMac вычисляется через OCRA-1 (HMAC-SHA256) на основе ECDH shared secret, а не CRC32. У тебя вообще нет ECDH key agreement.
#
#   ### 2. Нет ECDH key exchange
#
# �  В рефе на finish шаге:
#
#   1. Генерируется новая ECDH пара (generateECDH())
#   2. Её public key отправляется в guard.x509
#   3. Сервер возвращает свой public key в data.x509
#   4. Вызывается completeECDH(serverX509) — ECDH Diffie-Hellman → получается shared secret
#   5. Этот secret используется для computeTokenSnMac
#
#   У тебя в finish() — guard.x509 = твой статический public key (тот же что используется для подписей). Нужна отдельная ECDH пара для key exchange.
#
#   ### 3. X-Sign — body не включается в подпись
#
# �  Рабочий референс:
#
#     orgHeaders['X-Sign'] = computeXSign(orgUrl, orgHeaders, orgHeaders['X-SH'], orgPayload);
#     // ↑ body (4-й аргумент) хешируется вместе с заголовками
#
#     computeXSign = (url, headers, xshList, body) => {
#         // ...собрать строку из headers...
#         if (body) signText += '\n' + body;
#         const hash = sha256(signText);
#         return ecSign(hash);
#     };
#
#   Твой keys.py:67-81 — не принимает body вообще и не включает body в строку подписи. Для org-context-otp body нужен в подписи.
#
#   Плюс, у тебя compute_x_sign склеивает parts через "".join(parts), а в рефе используется "\n" разделитель (lines.join('\n')). И для url ты делаешь какую-то условную логику с
#   urlparse, а в рефе просто 'url:' + url.toLowerCase().
#   ──────
#   Итого, чтобы org-context-otp заработал, нужно:
#
#   1. Добавить ECDH key exchange в finish() — генерировать отдельную ECDH пару, отправлять её public key, а после ответа делать diffieHellman с серверным ключом → сохранять shared
#   secret
#   2. Переписать token_sn_mac() на OCRA-1 HMAC-SHA256 с этим shared secret
#   3. Исправить compute_x_sign() — добавить body в подпись, использовать \n разделитель и формат key:value
#

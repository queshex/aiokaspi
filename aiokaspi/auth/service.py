from __future__ import annotations

from typing import TYPE_CHECKING
from aiokaspi import exceptions as base_exceptions
from aiokaspi.auth import schemas, utils, validation
from aiokaspi.core import config, storage
from aiokaspi.core.keys import Keys
from aiokaspi.core.schemas import Entity, SessionSchema
from aiokaspi.core.storage import FileStorage

if TYPE_CHECKING:
    import aiohttp

    from aiokaspi.core.config import ConfigManager
    from aiokaspi.core.transport import Transport


class AuthClient:
    def __init__(
        self,
        transport: Transport | None = None,
        session: aiohttp.ClientSession | None = None,
        storage: storage.BaseStorage | None = None,
    ):
        if transport is None:
            if session is None:
                raise ValueError("Either transport or session must be provided")
            from aiokaspi.core.transport import Transport

            transport = Transport(session=session)
        self.transport = transport
        self.storage = storage or FileStorage()
        self.step: schemas.Step = schemas.Step.FIRST
        self.process_id: str | None = None
        self.config_manager: ConfigManager = config.ConfigManager(
            storage=self.storage,
        )
        self.authenticated: bool = self.config_manager.has_session

        self.config: schemas.Config = self.config_manager.get_lazy_config()

    def __str__(self) -> str:
        def mask(value: str | None) -> str:
            if value is None:
                return "None"
            return value[:2] + "*****" + value[-2:]

        return (
            f"AuthClient("
            f"public_key={mask(self.public_key)}, "
            f"private_key={mask(self.private_key)}, "
            f"pk={mask(self.pk)}, "
            f"pk_tag={mask(self.pk_tag)}, "
            f"device_id={mask(self.device_id)}, "
            f"install_id={mask(self.install_id)}, "
            f"pin_hash={mask(self.pin_hash)},"
            f"step={self.step}, "
            f"process_id={mask(self.process_id)}, "
            f"token_sn={mask(self.token_sn)}, "
            f"x509={mask(self.x509)}"
            f")"
        )

    def _refresh_config(self) -> None:
        self.config = self.config_manager.get_lazy_config()

    @staticmethod
    async def _is_valid_session(
        x509: str,
        token_sn: str,
        user_id_hash: str,
        device_id: str,
        install_id: str,
        pin_hash: str,
        public_key: str,
        private_key: str,
        pk: str,
        pk_tag: str,
    ) -> bool:
        "Заглушка, нужно доработать"
        return True

    def _check_step(self, step: schemas.Step) -> None:
        if self.step != step:
            raise base_exceptions.KaspiPayError(
                f"Incorrect step: {self.step}, expected {step}"
            )

    def _already_auth(self) -> None:
        if self.authenticated:
            raise base_exceptions.KaspiPayError(
                "You are already authenticated, but you call auth method"
            )

    async def me(self):
        url = "https://mtoken.kaspi.kz/v08/organizations/org-context-otp"
        secret = Keys.complete_ecdh(self.config.x509, self.config.private_key)
        sn_mac = Keys.token_sn_mac(self.config.token_sn, secret)
        pre_headers = schemas.PreContextHeaders(
            x_time=utils.get_current_time(),
            x_pktag=self.config.pk_tag,
            x_su=Keys.compute_x_su(url),
            x_kb_tokensn=self.config.token_sn,
            x_kb_client_ip=utils.get_local_ip(),
            x_install_id=self.config.install_id,
            x_kb_tokensnmac=sn_mac,
        )
        body = schemas.ContextRequestData(
            schemas.DeviceInformation(
                device_id=self.config.device_id, install_id=self.config.install_id
            )
        )

        x_sign = Keys.compute_x_sign(
            url=url,
            headers=pre_headers.asdict_with_aliases(),
            x_sh=pre_headers.x_sh,
            body=body,
            private_key=self.config.private_key,
        )
        headers = schemas.ContextHeaders.from_pre(pre_headers, x_sign)

        data: dict = await self.transport.post(
            base_url="https://mtoken.kaspi.kz",
            endpoint="/v08/organizations/org-context-otp",
            payload=body,
            headers=headers,
        )
        validation.ResponseValidator.expired_session(data)
        return data

    async def init(self) -> schemas.Meta:
        self._already_auth()
        self._check_step(schemas.Step.FIRST)

        body_data = schemas.FirstStepRequestData(
            device_id=self.config.device_id,
            install_id=self.config.install_id,
        )

        body = schemas.FirstStepRequest(
            data=body_data,
        )

        headers = schemas.StepHeaders(
            cookie=schemas.StepCookie(
                device_id=self.config.device_id,
                install_id=self.config.install_id,
                pk=self.config.pk,
                pk_tag=self.config.pk_tag,
            ),
            referer=body_data.referer,
        )

        data: dict = await self.transport.post(
            "api/v1/entrance/step",
            payload=body,
            headers=headers,
        )
        meta = validation.ResponseValidator.init(data)
        self.process_id = meta.p_id
        self.step = schemas.Step.SECOND
        return meta

    async def send_otp(self, phone_number: str) -> schemas.Meta:
        self._already_auth()
        self._check_step(schemas.Step.SECOND)

        otp_data = schemas.SecondStepRequestData(phone_number=phone_number)

        body = schemas.SecondStepRequest(
            meta=schemas.Meta(
                p_id=self.process_id,
                sn=schemas.SN.VIEW_ENTER_OTP,
            ),
            data=otp_data.asdict_with_aliases(),
        )

        headers = schemas.StepHeaders(
            cookie=schemas.StepCookie(
                device_id=self.config.device_id,
                install_id=self.config.install_id,
                pk=self.config.pk,
                pk_tag=self.config.pk_tag,
            ),
            referer=body.referer,
        )

        data: dict = await self.transport.post(
            "api/v1/entrance/step",
            payload=body,
            headers=headers,
        )
        self.step = schemas.Step.THIRD
        return validation.ResponseValidator.send_otp(data)

    async def confirm_otp(self, otp: str) -> schemas.Meta:
        self._already_auth()
        self._check_step(schemas.Step.THIRD)

        body = schemas.ThirdStepRequest(
            data=schemas.ThirdStepRequestData(user_otp=otp),
            meta=schemas.Meta(
                p_id=self.process_id,
                sn=schemas.SN.VIEW_ENTER_LOGIN_PASSWORD,
            ),
        )

        headers = schemas.StepHeaders(
            cookie=schemas.StepCookie(
                device_id=self.config.device_id,
                install_id=self.config.install_id,
                pk=self.config.pk,
                pk_tag=self.config.pk_tag,
            ),
            referer=body.referer,
        )

        data: dict = await self.transport.post(
            "api/v1/entrance/step",
            payload=body,
            headers=headers,
        )
        self.step = schemas.Step.FINISH
        return validation.ResponseValidator.confirm_otp(data)

    async def finish(self) -> schemas.FinishResponse:
        self._already_auth()
        self._check_step(schemas.Step.FINISH)

        data_to_sign = schemas.DataToSign(
            install_id=self.config.install_id,
            auth=[schemas.Auth()],
            time=utils.get_current_time(),
        )

        body = schemas.FinishRequest(
            guard=schemas.Guard(
                pin_hash=self.config.pin_hash, x509=self.config.public_key
            ),
            process_id=self.process_id,
            signed=schemas.Signed(
                data=data_to_sign.base64(),
                sign=Keys.sign_data(
                    data_to_sign.base64(), private_key=self.config.private_key
                ),
            ),
        )
        finish_url: str = f"{self.transport.base_url}/api/v1/kpentrance/finish"

        pre_headers = schemas.PreFinishHeaders(
            x_time=utils.get_current_time(),
            x_pktag=self.config.pk_tag,
            x_su=Keys.compute_x_su(url=finish_url),
        )
        pre_headers_dict = pre_headers.asdict_with_aliases()
        x_sign: str = Keys.compute_x_sign(
            url=finish_url,
            headers=pre_headers_dict,
            x_sh=pre_headers.x_sh,
            private_key=self.config.private_key,
        )

        headers = schemas.FinishHeaders.from_pre(pre_headers, x_sign=x_sign)

        data: dict = await self.transport.post(
            "api/v1/kpentrance/finish",
            payload=body,
            headers=headers,
        )
        result: schemas.FinishResponse = validation.ResponseValidator.finish(data)
        self.storage.save(
            entity=Entity.session,
            data=SessionSchema(
                x509=result.x509,
                token_sn=result.token_sn,
                user_id_hash=result.user_id_hash,
            ),
        )
        self._refresh_config()

    async def logout(self) -> None:
        pass

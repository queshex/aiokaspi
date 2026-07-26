from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from aiokaspi.auth import exceptions, schemas, utils, validation
from aiokaspi.auth.keys import Keys
from aiokaspi.auth.storage import Storage

if TYPE_CHECKING:
    import aiohttp
    from aiokaspi.auth.transport import Transport


class AuthClient:
    def __init__(
        self, 
        transport: Optional[Transport] = None,
        session: Optional[aiohttp.ClientSession] = None,
        public_key: Optional[str] = None,
        private_key: Optional[str] = None,
        pk: Optional[str] = None,
        pk_tag: Optional[str] = None,
        device_id: Optional[str] = None,
        install_id: Optional[str] = None,
        pin_hash: Optional[str] = None,
        x509: Optional[str] = None,
        token_sn: Optional[str] = None,
        user_id_hash: Optional[str] = None,
        raw_mode: bool = False,
    ):
        if transport is None:
            if session is None:
                raise ValueError("Either transport or session must be provided")
            from aiokaspi.auth.transport import Transport
            transport = Transport(session=session)
        self.transport = transport
        self._raw_mode: bool = raw_mode
        self.step: schemas.Step = schemas.Step.FIRST
        self.process_id: Optional[str] = None
        self.authenticated: bool = False

        self.public_key: str = public_key
        self.private_key: str = private_key
        self.pk: str = pk
        self.pk_tag: str = pk_tag
        self.device_id: str = device_id
        self.install_id: str = install_id
        self.pin_hash: str = pin_hash

        self.token_sn: str = token_sn
        self.x509: str = x509
        self.user_id_hash: str = user_id_hash
    
    def __str__(self) -> str:
        def mask(value: Optional[str]) -> str:
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
                f"pin_hash={mask(self.pin_hash)}, "
                f"raw_mode={self._raw_mode}, "
                f"step={self.step}, "
                f"process_id={mask(self.process_id)}, "
                f"token_sn={mask(self.token_sn)}, "
                f"x509={mask(self.x509)}"
            f")"
        )

    @classmethod
    async def from_files(
        cls, 
        transport: Optional[Transport] = None, 
        session: Optional[aiohttp.ClientSession] = None,
        raw_mode: bool = False, 
        with_session: bool = True
    ) -> AuthClient:
        if transport is None:
            if session is None:
                raise ValueError("Either transport or session must be provided")
            from aiokaspi.auth.transport import Transport
            transport = Transport(session=session)

        if not Storage.check_keys():
            Storage.save_keys(*Keys.generate_keypair_base64())
        if not Storage.check_device():
            Storage.save_device(
                Keys.generate_upper_uuid(),
                Keys.generate_upper_uuid(),
                Keys.generate_pin_hash(),
            )

        self = cls(transport=transport, raw_mode=raw_mode)

        if with_session:
            if not Storage.check_session():
                raise exceptions.KaspiPayError("Session not found")
            self.x509, self.token_sn, self.user_id_hash = Storage.get_session()

        self.private_key, self.public_key = Storage.get_keys()
        self.device_id, self.install_id, self.pin_hash = Storage.get_device()
        self.pk = Keys.get_pk(self.public_key)
        self.pk_tag = Keys.get_pk_tag(self.public_key)

        if with_session:
            if await self._is_valid_session(
                self.x509, 
                self.token_sn, 
                self.user_id_hash, 
                self.device_id, 
                self.install_id, 
                self.pin_hash, 
                self.public_key,
                self.private_key,
                self.pk,
                self.pk_tag,
            ):
                self.authenticated = True
                return self
            raise exceptions.KaspiPayError("Session is not valid")
        return self

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
            raise exceptions.KaspiPayError(f"Incorrect step: {self.step}, expected {step}")
    
    def _already_auth(self) -> None:
        if self.authenticated:
            raise exceptions.KaspiPayError("You are already authenticated, but you call auth method")
    
    async def me(self):
        pass
        
    async def init(self) -> schemas.Meta:
        self._already_auth()
        self._check_step(schemas.Step.FIRST)
            
        body_data = schemas.FirstStepRequestData(
            device_id=self.device_id,
            install_id=self.install_id,
        )   

        body = schemas.FirstStepRequest(
            data=body_data,
        )

        headers = schemas.StepHeaders(
            cookie=schemas.StepCookie(
                device_id=self.device_id,
                install_id=self.install_id,
                pk=self.pk,
                pk_tag=self.pk_tag,
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
        return meta if not self._raw_mode else data
        

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
                device_id=self.device_id,
                install_id=self.install_id,
                pk=self.pk,
                pk_tag=self.pk_tag,
            ),
            referer=body.referer,
        )

        data: dict = await self.transport.post(
            "api/v1/entrance/step",
            payload=body,
            headers=headers,
        )
        self.step = schemas.Step.THIRD
        return validation.ResponseValidator.send_otp(data) if not self._raw_mode else data

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
                device_id=self.device_id,
                install_id=self.install_id,
                pk=self.pk,
                pk_tag=self.pk_tag,
            ),
            referer=body.referer,
        )

        data: dict = await self.transport.post(
            "api/v1/entrance/step",
            payload=body,
            headers=headers,
        )
        self.step = schemas.Step.FINISH
        return validation.ResponseValidator.confirm_otp(data) if not self._raw_mode else data

    async def finish(self) -> schemas.FinishResponse:
        self._already_auth()
        self._check_step(schemas.Step.FINISH)

        data_to_sign = schemas.DataToSign(
            install_id=self.install_id,
            auth=[
                schemas.Auth()
            ],
            time=utils.get_current_time()
        )
        
        body = schemas.FinishRequest(
            guard=schemas.Guard(pin_hash=self.pin_hash, x509=self.public_key),
            process_id=self.process_id,
            signed=schemas.Signed(
                data=data_to_sign.base64(),
                sign=Keys.sign_data(data_to_sign.base64(), private_key=self.private_key)
            ),
        )
        finish_url: str = f"{self.transport.base_url}/api/v1/kpentrance/finish"

        pre_headers = schemas.PreFinishHeaders(
            x_time=utils.get_current_time(),
            x_pktag=self.pk_tag,
            x_su=Keys.compute_x_su(url=finish_url)
        )
        pre_headers_dict = pre_headers.asdict_with_aliases()
        x_sign: str = Keys.compute_x_sign(
            url=finish_url, 
            headers=pre_headers_dict, 
            x_sh=pre_headers.x_sh,
            private_key=self.private_key,
        )

        headers = schemas.FinishHeaders.from_pre(pre_headers, x_sign=x_sign)

        data: dict = await self.transport.post(
            "api/v1/kpentrance/finish",
            payload=body,
            headers=headers,
        )
        result: schemas.FinishResponse = validation.ResponseValidator.finish(data) 
        Storage.save_session(
            x509=result.x509, 
            token_sn=result.token_sn, 
            user_id_hash=result.user_id_hash
        )
        self.token_sn = result.token_sn
        self.x509 = result.x509
        self.user_id_hash = result.user_id_hash
        self.authenticated = True
        return result if not self._raw_mode else data

    async def logout(self) -> None:
        #TODO: Закончить
        body = schemas.LogoutRequest(
            device_id=self.device_id,
            token_sn=self.token_sn,
        )

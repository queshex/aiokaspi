from aiokaspi.auth import schemas, exceptions


class ResponseValidator:
    @staticmethod
    def init(data: dict) -> schemas.Meta:
        if data.get("status") == 400:
            raise exceptions.BadRequestError("Bad incoming request. Please try again")
        if data["view"].get("onOpenAlarm", {}).get("error") is not None:
            match data["view"]["onOpenAlarm"]["error"]["code"]:
                case schemas.ErrorCode.OLD_VERSION_TO_UPDATE:
                    raise exceptions.UpdateClientError(
                        "Update client, you can do this in config"
                    )
                case schemas.ErrorCode.TEMPORARY_BLOCKED:
                    raise exceptions.TemporaryBlockedError(
                        "Your account has been temporarily blocked."
                    )
                case _:
                    raise exceptions.UnexpectedResponseError(data)
        meta = schemas.Meta.from_dict(data["meta"])
        match meta.sn:
            case schemas.SN.ENTER_PHONE_NUMBER:
                return meta
            case _:
                raise exceptions.UnexpectedResponseError(data)

    @staticmethod
    def send_otp(data: dict) -> schemas.Meta:
        meta = schemas.Meta.from_dict(data["meta"])

        view_error_code = (
            data.get("view", {}).get("onOpenAlarm", {}).get("error", {}).get("code")
        )
        if view_error_code is not None:
            match view_error_code:
                case schemas.ErrorCode.TEMPORARY_BLOCKED:
                    raise exceptions.TemporaryBlockedError(
                        "Your account has been temporarily blocked."
                    )
                case _:
                    raise exceptions.UnexpectedResponseError(data)

        if data.get("error") is not None:
            error_code = data["error"]["code"]
            match error_code:
                case schemas.ErrorCode.CONTEXT_NOT_FOUND:
                    raise exceptions.TimeExceededError(
                        "Your time has exceeded. Please try again."
                    )
                case schemas.ErrorCode.BAD_REQUEST:
                    raise exceptions.BadRequestError("Bad request.")
                case schemas.ErrorCode.INVALID_PHONE_NUMBER:
                    raise exceptions.InvalidPhoneNumberError(
                        "Invalid phone number provided."
                    )
                # case schemas.ErrorCode.SYSTEM_ERROR:
                #     raise exceptions.BadRequestError()
                case _:
                    raise exceptions.UnexpectedResponseError(data)

        match meta.sn:
            case schemas.SN.VIEW_ENTER_LOGIN_PASSWORD:
                raise exceptions.NotCashierError(
                    "You are not a cashier. Please register your number as Cashier in Kaspi.kz application."
                )
            case schemas.SN.WEB_ORG_REGISTRATION:
                raise exceptions.OrganizationNotCreatedError(
                    "Organization not created."
                )
            case schemas.SN.VIEW_ENTER_OTP:
                return meta
            case _:
                raise exceptions.UnexpectedResponseError(data)

    @staticmethod
    def confirm_otp(data: dict) -> schemas.Meta:
        if data.get("error") is not None:
            match data["error"]["code"]:
                case schemas.ErrorCode.INVALID_OTP:
                    raise exceptions.InvalidOtpError("Your OTP is incorrect.")
                case _:
                    raise exceptions.UnexpectedResponseError(data)
        meta = schemas.Meta.from_dict(data["meta"])

        match meta.sn:
            case schemas.SN.MOBILE_DEVICE_REGISTRATION:
                return meta
            case _:
                raise exceptions.UnexpectedResponseError(data)

    @staticmethod
    def finish(data: dict) -> schemas.FinishResponse:
        if (data.get("success") is True) and (
            data.get("data", {}).get("success") is True
        ):
            return schemas.FinishResponse.from_dict(data["data"])
        raise exceptions.UnexpectedResponseError(data)

from typing import Optional

class Base(Exception):
    def __init__(self, details: Optional[str] = None):
        self.details = details
        super().__init__(details)

class KaspiPayError(Base):
    pass
    
class BadRequestError(Base):
    pass

class UnexpectedResponseError(Exception):
    def __init__(self, data: dict):
        self.data = f"Unexpected response, please report this error to developers. Raw response: {data}"
        super().__init__(self.data) 

class InvalidPhoneNumberError(Base):
    pass

class NotCashierError(Base):
    pass

class TimeExceededError(Base):
    pass

class OrganizationNotCreatedError(Base):
    pass

class InvalidOtpError(Base):
    pass

class ManyAttemptsError(Base):
    pass

class TemporaryBlockedError(Base):
    pass

class UpdateClientError(Base):
    pass

class ContextNotFoundError(Base):
    pass

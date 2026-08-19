from aiokaspi.exceptions import Base


class InvalidPhoneNumberError(Base):
    pass


class NotCashierError(Base):
    pass


class OrganizationNotCreatedError(Base):
    pass


class InvalidOtpError(Base):
    pass

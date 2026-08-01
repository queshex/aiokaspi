class Base(Exception):
    def __init__(self, details: str | None = None):
        self.details = details
        super().__init__(details)


class KaspiPayError(Base):
    pass

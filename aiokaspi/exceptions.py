from typing import Optional


class Base(Exception):
    def __init__(self, details: Optional[str] = None):
        self.details = details
        super().__init__(details)


class KaspiPayError(Base):
    pass

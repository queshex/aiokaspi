from typing import Optional

import aiohttp

from aiokaspi.auth.schemas import BaseSchema


class Transport:
    def __init__(
        self, 
        session: aiohttp.ClientSession,
        base_url: str = "https://entrance-pay.kaspi.kz"
    ) -> None:
        self.session = session
        self.base_url = base_url
    
    async def get(self, endpoint: str, headers: type[BaseSchema], params: Optional[type[BaseSchema]] = None) -> dict:
        async with self.session.get(
            f"{self.base_url}/{endpoint}", 
            headers=headers.asdict_with_aliases(), 
            params=params.asdict_with_aliases() if params else None
        ) as response:
            return await response.json()

    async def post(self, endpoint: str, headers: type[BaseSchema], payload: type[BaseSchema]) -> dict:
        async with self.session.post(
            f"{self.base_url}/{endpoint}", 
            headers=headers.asdict_with_aliases(), 
            json=payload.asdict_with_aliases()
        ) as response:
            return await response.json()

import aiohttp
import logging

logger = logging.getLogger(__name__)


class Transport:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str = "https://entrance-pay.kaspi.kz",
    ) -> None:
        self.session = session
        self.base_url = base_url

    async def get(
        self,
        endpoint: str,
        headers,
        params=None,
    ) -> dict:
        async with self.session.get(
            f"{self.base_url}/{endpoint}",
            headers=headers.asdict_with_aliases(),
            params=params.asdict_with_aliases() if params else None,
        ) as response:
            raw_text = await response.text()
            logger.debug(
                "GET %s status=%s raw_body=%s", endpoint, response.status, raw_text
            )
            return await response.json()

    async def post(self, endpoint: str, headers, payload, base_url=None) -> dict:
        async with self.session.post(
            f"{base_url if base_url else self.base_url}{endpoint}",
            headers=headers.asdict_with_aliases(),
            json=payload.asdict_with_aliases(),
        ) as response:
            logger.debug("SENDING: headers=%s body=%s", headers, payload)
            raw_text = await response.text()
            logger.debug(
                "POST %s status=%s raw_body=%s", endpoint, response.status, raw_text
            )
            return await response.json()

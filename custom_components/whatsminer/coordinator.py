import json
import logging
from datetime import timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import WhatsminerAPI
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_PASSWORD


@dataclass
class MinerData(object):
    device_model: str
    pools: Dict[str, Any]
    summary: Dict[str, Any]


class WhatsminerCoordinator(DataUpdateCoordinator[MinerData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            update_method=self.async_fetch,
            update_interval=timedelta(seconds=5)
        )

        host = entry.data[CONF_HOST]
        port = entry.data[CONF_PORT]
        password = entry.data[CONF_PASSWORD]
        self.miner: WhatsminerAPI = WhatsminerAPI(host, port, password)
        self.device_model: Optional[str] = None

    async def async_fetch(self) -> MinerData:
        try:
            if self.device_model is None:
                async with async_timeout.timeout(10):
                    details = await self.miner.read(cmd="devdetails")
                    self.device_model = details["DEVDETAILS0"]["Model"]

            async with async_timeout.timeout(10):
                summary = await self.miner.read(cmd="summary")
            async with async_timeout.timeout(10):
                pools = await self.miner.read(cmd="pools")
            return MinerData(self.device_model, pools, summary)

        except json.JSONDecodeError as err:
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

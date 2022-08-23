import json
import logging
from datetime import timedelta
from typing import Optional, Dict

import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import WhatsminerAPI
from .const import DOMAIN, MINER


class WhatsminerCoordinator(DataUpdateCoordinator[Dict]):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            update_method=self.async_fetch,
            update_interval=timedelta(seconds=10)
        )
        self.miner: WhatsminerAPI = hass.data[DOMAIN][entry.entry_id][MINER]
        self.device_model: Optional[str] = None

    async def async_fetch(self):
        try:
            if self.device_model is None:
                async with async_timeout.timeout(10):
                    details = await self.miner.read(cmd="devdetails")
                    self.device_model = details["DEVDETAILS0"]["Model"]

            data = {}
            async with async_timeout.timeout(10):
                data["summary"] = self.miner.read(cmd="summary")
            async with async_timeout.timeout(10):
                data["pools"] = self.miner.read(cmd="pools")
            return data
        except json.JSONDecodeError as err:
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

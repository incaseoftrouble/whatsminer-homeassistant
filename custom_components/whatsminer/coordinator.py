import dataclasses
import json
import logging
from datetime import timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import WhatsminerAPI
from .const import DOMAIN, MINER


@dataclass
class MinerData(object):
    device_model: str
    pools: Dict[str, Any]
    summary: Dict[str, Any]


class WhatsminerCoordinator(DataUpdateCoordinator[MinerData]):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            update_method=self.async_fetch,
            update_interval=timedelta(seconds=5)
        )
        self.miner: WhatsminerAPI = hass.data[DOMAIN][entry.entry_id][MINER]
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

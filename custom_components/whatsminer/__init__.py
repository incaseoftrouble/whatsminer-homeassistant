"""
Expose Whatsminer to HA
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Optional

import async_timeout
import voluptuous as vol
import whatsminer
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, COORDINATOR, TOKEN

_LOGGER = logging.getLogger(__name__)


async def get_coordinator(
        hass: HomeAssistant,
        entry: ConfigEntry,
) -> DataUpdateCoordinator:
    if COORDINATOR in hass.data[DOMAIN][entry.entry_id]:
        return hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    hass.data[DOMAIN][entry.entry_id][COORDINATOR] = Coordinator(hass, entry)

    await hass.data[DOMAIN][entry.entry_id][COORDINATOR].async_refresh()
    return hass.data[DOMAIN][entry.entry_id][COORDINATOR]


class Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            update_method=self.async_fetch,
            update_interval=timedelta(seconds=10)
        )
        self.token = hass.data[DOMAIN][entry.entry_id][TOKEN]
        self.device_model: Optional[str] = None

    async def async_fetch(self):
        try:
            if self.device_model is None:
                async with async_timeout.timeout(10):
                    details = whatsminer.WhatsminerAPI.get_read_only_info(self.token, cmd="devdetails")
                    self.device_model = details["DEVDETAILS0"]["Model"]

            data = {}
            async with async_timeout.timeout(10):
                data["summary"] = whatsminer.WhatsminerAPI.get_read_only_info(self.token, cmd="summary")
            async with async_timeout.timeout(10):
                data["pools"] = whatsminer.WhatsminerAPI.get_read_only_info(self.token, cmd="pools")
            return data
        except json.JSONDecodeError as err:
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

"""
Expose Whatsminer to HA
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import WhatsminerMachine
from .const import DOMAIN, COORDINATOR, MINER
from .coordinator import WhatsminerCoordinator

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    miner_coordinator = WhatsminerCoordinator(hass, entry)
    await miner_coordinator.async_refresh()
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})[
        COORDINATOR
    ] = miner_coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    # entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
#    await hass.config_entries.async_reload(entry.entry_id)

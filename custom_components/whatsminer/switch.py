import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from . import WhatsminerCoordinator
from .const import DOMAIN, COORDINATOR
from .coordinator import OnlineMinerData
from .entity import WhatsminerEntity


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WhatsminerCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    async_add_entities([
        MinerSwitch(coordinator)
    ])


class MinerSwitch(WhatsminerEntity, SwitchEntity):
    def __init__(self, coordinator):
        super(WhatsminerEntity, self).__init__(coordinator=coordinator)
        self.entity_description = SwitchEntityDescription(
            key="power",
            name="Power",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self) -> bool:
        return isinstance(self.coordinator.data, OnlineMinerData)

    def turn_off(self) -> None:
        raise NotImplemented

    def turn_on(self) -> None:
        raise NotImplemented

    async def async_turn_on(self) -> None:
        await self.coordinator.api.power_on_miner()

    async def async_turn_off(self) -> None:
        await self.coordinator.api.power_off_miner()

import logging

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WhatsminerCoordinator
from .const import DOMAIN
from .coordinator import OnlineMinerData


class WhatsminerEntity(CoordinatorEntity[WhatsminerCoordinator]):
    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_mac)},
            connections={(CONNECTION_NETWORK_MAC, self.coordinator.device_mac)},
            configuration_url=f"https://{self.coordinator.device_host}",
            name=f"Miner {self.coordinator.device_mac}",
            manufacturer="Whatsminer",
            model=self.coordinator.device_model,
        )

    @property
    def has_entity_name(self) -> bool:
        return True


class OnlineWhatsminerEntity(WhatsminerEntity):
    @property
    def available(self) -> bool:
        return super(WhatsminerEntity, self).available and isinstance(
            self.coordinator.data, OnlineMinerData
        )

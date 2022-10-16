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
            identifiers={
                (DOMAIN, self.unique_id)
            },
            connections={(CONNECTION_NETWORK_MAC, self.coordinator.device_mac)},
            configuration_url=f"http://{self.coordinator.device_host}",
            name=self.name,
            manufacturer="Whatsminer",
            model=self.coordinator.device_model,
        )


class OnlineWhatsminerEntity(WhatsminerEntity):
    @property
    def available(self) -> bool:
        return super(WhatsminerEntity, self).available and isinstance(self.coordinator.data, OnlineMinerData)

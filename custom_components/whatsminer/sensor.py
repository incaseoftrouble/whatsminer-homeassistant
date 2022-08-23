from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import FREQUENCY_MEGAHERTZ
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, COORDINATOR


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    async_add_entities(
        [HashRateSensor(coordinator)]
    )


class HashRateSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Average Hash Rate"
    _attr_native_unit_of_measurement = FREQUENCY_MEGAHERTZ
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
            "manufacturer": "Whatsminer",
            "model": self.coordinator.device_model,
            "sw_version": self.coordinator.data[""]
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        value = self.coordinator.data.get("MHS av", None)
        self._attr_native_value = value if value is None else float(value)
        self.async_write_ha_state()

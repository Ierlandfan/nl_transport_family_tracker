"""Binary sensor platform for Family Transport Tracker."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FamilyTransportCoordinator
from .const import DOMAIN, STATUS_ON_ROUTE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    sensors = []
    for person_config in entry.data.get("people", []):
        person_entity = person_config["person"]
        sensors.append(OnPlannedRouteSensor(coordinator, person_entity))
    
    async_add_entities(sensors)


class OnPlannedRouteSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for on planned route."""

    def __init__(self, coordinator: FamilyTransportCoordinator, person_entity: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._person_entity = person_entity
        self._attr_unique_id = f"{DOMAIN}_{person_entity}_on_route"
        self._attr_name = f"{person_entity.split('.')[-1].title()} On Planned Route"

    @property
    def is_on(self):
        """Return true if on planned route."""
        data = self.coordinator.data.get(self._person_entity, {})
        return data.get("status") == STATUS_ON_ROUTE

    @property
    def extra_state_attributes(self):
        """Return attributes."""
        data = self.coordinator.data.get(self._person_entity, {})
        return {
            "confidence": data.get("confidence"),
            "planned_route": data.get("planned_route"),
        }

    @property
    def icon(self):
        """Return icon."""
        return "mdi:check-circle" if self.is_on else "mdi:close-circle"

"""Sensor platform for Family Transport Tracker."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FamilyTransportCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    sensors = []
    for person_config in entry.data.get("people", []):
        person_entity = person_config["person"]
        sensors.append(TransportStatusSensor(coordinator, person_entity))
        sensors.append(TransportETASensor(coordinator, person_entity))
    
    async_add_entities(sensors)


class TransportStatusSensor(CoordinatorEntity, SensorEntity):
    """Transport status sensor."""

    def __init__(self, coordinator: FamilyTransportCoordinator, person_entity: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._person_entity = person_entity
        self._attr_unique_id = f"{DOMAIN}_{person_entity}_status"
        self._attr_name = f"{person_entity.split('.')[-1].title()} Transport Status"

    @property
    def native_value(self):
        """Return the state."""
        data = self.coordinator.data.get(self._person_entity, {})
        return data.get("status", "Unknown")

    @property
    def extra_state_attributes(self):
        """Return attributes."""
        data = self.coordinator.data.get(self._person_entity, {})
        return {
            "planned_route": data.get("planned_route"),
            "departure_time": data.get("departure_time"),
            "expected_arrival": data.get("expected_arrival"),
            "delay_minutes": data.get("delay_minutes"),
            "confidence": data.get("confidence"),
            "travel_mode": data.get("travel_mode"),
            "left_on_time": data.get("left_on_time"),
            "driving_speed": data.get("driving_speed"),
            "car_eta": data.get("car_eta"),
            "stop_duration": data.get("stop_duration"),
            "stop_address": data.get("address"),
            "detour_location": data.get("detour_location"),
        }

    @property
    def icon(self):
        """Return icon."""
        status = self.native_value
        if status == "On Route":
            return "mdi:train-car"
        elif status == "Missed":
            return "mdi:alert"
        elif status == "At Station":
            return "mdi:train-station"
        elif status == "By Car":
            return "mdi:car"
        elif status == "Stopped":
            return "mdi:map-marker-alert"
        elif status == "Detoured":
            return "mdi:map-marker-question"
        return "mdi:help"


class TransportETASensor(CoordinatorEntity, SensorEntity):
    """Transport ETA sensor."""

    def __init__(self, coordinator: FamilyTransportCoordinator, person_entity: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._person_entity = person_entity
        self._attr_unique_id = f"{DOMAIN}_{person_entity}_eta"
        self._attr_name = f"{person_entity.split('.')[-1].title()} Transport ETA"

    @property
    def native_value(self):
        """Return the state."""
        data = self.coordinator.data.get(self._person_entity, {})
        return data.get("expected_arrival")

    @property
    def extra_state_attributes(self):
        """Return attributes."""
        data = self.coordinator.data.get(self._person_entity, {})
        return {
            "delay": data.get("delay_minutes"),
            "next_station": data.get("next_station"),
        }

    @property
    def icon(self):
        """Return icon."""
        return "mdi:clock-outline"

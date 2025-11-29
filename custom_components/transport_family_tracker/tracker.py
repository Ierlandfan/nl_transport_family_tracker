"""Family transport tracking logic."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.util import dt as dt_util
from homeassistant.components.zone import DOMAIN as ZONE_DOMAIN

from .const import (
    STATUS_ON_ROUTE,
    STATUS_MISSED,
    STATUS_DELAYED,
    STATUS_NOT_TRAVELING,
    STATUS_AT_STATION,
    STATUS_BY_CAR,
    STATUS_STOPPED,
    STATUS_DETOURED,
    SPEED_THRESHOLD_DRIVING,
    SPEED_THRESHOLD_STOPPED,
)
from .schedule import should_show_route

_LOGGER = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in meters."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth radius in meters
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


class FamilyTransportTracker:
    """Track family members on transport routes."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        """Initialize the tracker."""
        self.hass = hass
        self.config_entry = config_entry
        self.people_data = {}
        self.previous_locations = {}
        self.stop_times = {}
        self.detour_locations = {}

    async def async_update(self) -> dict[str, Any]:
        """Update tracking data for all people."""
        data = {}
        
        for person_config in self.config_entry.data.get("people", []):
            person_entity = person_config["person"]
            person_data = await self._track_person(person_config)
            data[person_entity] = person_data
        
        return data

    async def _track_person(self, person_config: dict) -> dict[str, Any]:
        """Track a single person."""
        person_entity = person_config["person"]
        person_state = self.hass.states.get(person_entity)
        
        if not person_state:
            return self._get_default_data()
        
        # Get person's current location and movement data
        lat = person_state.attributes.get("latitude")
        lon = person_state.attributes.get("longitude")
        speed = person_state.attributes.get("speed", 0)
        driving = person_state.attributes.get("driving", False)
        address = person_state.attributes.get("address", "Unknown")
        
        if not lat or not lon:
            return self._get_default_data()
        
        # Determine which route they should be on based on time
        current_time = dt_util.now()
        route_entity = self._get_expected_route(person_config, current_time)
        
        if not route_entity:
            return {
                "status": STATUS_NOT_TRAVELING,
                "planned_route": None,
                "current_location": {"lat": lat, "lon": lon},
                "confidence": 100,
            }
        
        # Get route information
        route_state = self.hass.states.get(route_entity)
        if not route_state:
            return self._get_default_data()
        
        origin = route_state.attributes.get("origin", "")
        destination = route_state.attributes.get("destination", "")
        planned_route = f"{origin} → {destination}"
        
        # Check if traveling by car instead of public transport
        car_status = await self._check_car_travel(
            person_entity, lat, lon, speed, driving, route_state
        )
        
        if car_status:
            return {
                **car_status,
                "planned_route": planned_route,
                "current_location": {"lat": lat, "lon": lon},
                "address": address,
            }
        
        # Check if at station, en route, or missed
        status = await self._determine_status(
            lat, lon, route_state, person_config
        )
        
        return {
            "status": status["status"],
            "planned_route": planned_route,
            "current_location": {"lat": lat, "lon": lon},
            "departure_time": route_state.attributes.get("departure_time"),
            "expected_arrival": route_state.attributes.get("arrival_time"),
            "delay_minutes": route_state.attributes.get("delay", 0),
            "confidence": status["confidence"],
            "next_station": status.get("next_station"),
            "travel_mode": "public_transport",
            "address": address,
        }

    def _get_expected_route(self, person_config: dict, current_time: datetime) -> str | None:
        """Determine which route the person should be on."""
        from datetime import time as dt_time
        
        current_time_only = current_time.time()
        
        # Check morning route
        if person_config.get("morning_route"):
            morning_schedule = {
                "days": person_config.get("morning_days", ["mon", "tue", "wed", "thu", "fri"]),
                "exclude_holidays": person_config.get("morning_exclude_holidays", True),
                "custom_exclude_dates": person_config.get("morning_custom_exclude_dates", ""),
                "departure_time": person_config.get("morning_departure_time"),
            }
            if should_show_route(morning_schedule, current_time):
                return person_config["morning_route"]
        
        # Check evening route
        if person_config.get("evening_route"):
            evening_schedule = {
                "days": person_config.get("evening_days", ["mon", "tue", "wed", "thu", "fri"]),
                "exclude_holidays": person_config.get("evening_exclude_holidays", True),
                "custom_exclude_dates": person_config.get("evening_custom_exclude_dates", ""),
                "departure_time": person_config.get("evening_departure_time"),
            }
            if should_show_route(evening_schedule, current_time):
                return person_config["evening_route"]
        
        return None

    async def _determine_status(
        self, lat: float, lon: float, route_state: State, person_config: dict
    ) -> dict:
        """Determine person's transport status."""
        # Get station coordinates from route
        route_coords = route_state.attributes.get("route_coordinates", [])
        
        if not route_coords:
            return {"status": STATUS_NOT_TRAVELING, "confidence": 50}
        
        origin_coords = route_coords[0] if route_coords else None
        
        if not origin_coords:
            return {"status": STATUS_NOT_TRAVELING, "confidence": 50}
        
        # Check if at station
        station_radius = self.config_entry.data.get("station_radius", 100)
        distance_to_origin = calculate_distance(
            lat, lon, origin_coords[0], origin_coords[1]
        )
        
        at_station = distance_to_origin <= station_radius
        
        # Get departure time
        departure_str = route_state.attributes.get("departure_time")
        if not departure_str:
            return {"status": STATUS_NOT_TRAVELING, "confidence": 50}
        
        # Check if transport departed
        current_time = dt_util.now()
        departure_window = self.config_entry.data.get("departure_window", 5)
        
        # Simple logic for demo
        if at_station:
            return {
                "status": STATUS_AT_STATION,
                "confidence": 90,
            }
        
        # Check if on route (simplified)
        for coord in route_coords:
            dist = calculate_distance(lat, lon, coord[0], coord[1])
            if dist <= self.config_entry.data.get("route_tolerance", 500):
                return {
                    "status": STATUS_ON_ROUTE,
                    "confidence": 85,
                }
        
        return {
            "status": STATUS_NOT_TRAVELING,
            "confidence": 70,
        }

    async def _check_car_travel(
        self,
        person_entity: str,
        lat: float,
        lon: float,
        speed: float,
        driving: bool,
        route_state: State,
    ) -> dict | None:
        """Check if person is traveling by car instead of public transport."""
        current_time = dt_util.now()
        
        # Get expected departure and destination
        route_coords = route_state.attributes.get("route_coordinates", [])
        if not route_coords:
            return None
        
        origin_coords = route_coords[0]
        dest_coords = route_coords[-1]
        
        # Check if person is driving
        is_driving = driving or speed > SPEED_THRESHOLD_DRIVING
        
        if not is_driving:
            # Check if stopped somewhere
            if speed < SPEED_THRESHOLD_STOPPED:
                return await self._check_stop(person_entity, lat, lon)
            return None
        
        # Person is driving - check if they left origin area
        station_radius = self.config_entry.data.get("station_radius", 100)
        distance_from_origin = calculate_distance(
            lat, lon, origin_coords[0], origin_coords[1]
        )
        
        left_on_time = False
        if distance_from_origin > station_radius:
            # They left the origin area
            departure_time_str = route_state.attributes.get("departure_time")
            if departure_time_str:
                # Check if they left around the expected time
                left_on_time = True  # Simplified
        
        # Calculate ETA by car
        distance_to_dest = calculate_distance(
            lat, lon, dest_coords[0], dest_coords[1]
        )
        
        # Estimate arrival (simplified: assume 50 km/h average)
        if speed > 0:
            hours_remaining = (distance_to_dest / 1000) / 50
            eta = current_time + timedelta(hours=hours_remaining)
        else:
            eta = None
        
        # Check if this is a detour
        distance_to_route = self._distance_to_route_line(lat, lon, route_coords)
        is_detour = distance_to_route > 1000  # 1km off route
        
        if is_detour:
            self.detour_locations[person_entity] = {
                "lat": lat,
                "lon": lon,
                "time": current_time,
            }
        
        return {
            "status": STATUS_DETOURED if is_detour else STATUS_BY_CAR,
            "travel_mode": "car",
            "left_on_time": left_on_time,
            "driving_speed": speed,
            "car_eta": eta.isoformat() if eta else None,
            "confidence": 90,
            "detour_location": self.detour_locations.get(person_entity),
        }

    async def _check_stop(self, person_entity: str, lat: float, lon: float) -> dict | None:
        """Check if person has stopped at a location."""
        current_time = dt_util.now()
        
        if person_entity not in self.stop_times:
            self.stop_times[person_entity] = {
                "lat": lat,
                "lon": lon,
                "time": current_time,
            }
            return None
        
        stop_data = self.stop_times[person_entity]
        
        # Check if still at same location
        distance_moved = calculate_distance(
            lat, lon, stop_data["lat"], stop_data["lon"]
        )
        
        if distance_moved < 50:  # Still within 50m
            duration = (current_time - stop_data["time"]).total_seconds() / 60
            
            if duration > 5:  # Stopped for more than 5 minutes
                # Get address via reverse geocoding (simplified - just use Life360's address)
                return {
                    "status": STATUS_STOPPED,
                    "travel_mode": "stopped",
                    "stop_duration": int(duration),
                    "confidence": 95,
                }
        else:
            # Moved - reset stop timer
            del self.stop_times[person_entity]
        
        return None

    def _distance_to_route_line(self, lat: float, lon: float, route_coords: list) -> float:
        """Calculate minimum distance from point to route line."""
        if not route_coords:
            return float('inf')
        
        min_distance = float('inf')
        for coord in route_coords:
            dist = calculate_distance(lat, lon, coord[0], coord[1])
            min_distance = min(min_distance, dist)
        
        return min_distance

    def _get_default_data(self) -> dict:
        """Return default tracking data."""
        return {
            "status": STATUS_NOT_TRAVELING,
            "planned_route": None,
            "current_location": None,
            "confidence": 0,
            "travel_mode": "unknown",
        }

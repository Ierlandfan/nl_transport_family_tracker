"""Config flow for Family Transport Tracker."""
from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    CONF_PERSON,
    CONF_MORNING_ROUTE,
    CONF_EVENING_ROUTE,
    CONF_NOTIFY,
    CONF_STATION_RADIUS,
    CONF_ROUTE_TOLERANCE,
    CONF_DEPARTURE_WINDOW,
    DEFAULT_STATION_RADIUS,
    DEFAULT_ROUTE_TOLERANCE,
    DEFAULT_DEPARTURE_WINDOW,
)


class FamilyTransportTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Family Transport Tracker."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.people = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_show_menu(
                step_id="user",
                menu_options=["add_person", "finish"],
            )
        return self.async_show_menu(
            step_id="user",
            menu_options=["add_person", "finish"],
        )

    async def async_step_add_person(self, user_input=None):
        """Add a person to track."""
        errors = {}
        
        if user_input is not None:
            self.people.append(user_input)
            return await self.async_step_user()

        return self.async_show_form(
            step_id="add_person",
            data_schema=vol.Schema({
                vol.Required(CONF_PERSON): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                ),
                vol.Optional(CONF_MORNING_ROUTE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("morning_departure_time"): selector.TimeSelector(),
                vol.Optional("morning_days", default=["mon", "tue", "wed", "thu", "fri"]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "mon", "label": "Monday"},
                            {"value": "tue", "label": "Tuesday"},
                            {"value": "wed", "label": "Wednesday"},
                            {"value": "thu", "label": "Thursday"},
                            {"value": "fri", "label": "Friday"},
                            {"value": "sat", "label": "Saturday"},
                            {"value": "sun", "label": "Sunday"},
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("morning_exclude_holidays", default=True): bool,
                vol.Optional("morning_custom_exclude_dates"): str,
                vol.Optional(CONF_EVENING_ROUTE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("evening_departure_time"): selector.TimeSelector(),
                vol.Optional("evening_days", default=["mon", "tue", "wed", "thu", "fri"]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "mon", "label": "Monday"},
                            {"value": "tue", "label": "Tuesday"},
                            {"value": "wed", "label": "Wednesday"},
                            {"value": "thu", "label": "Thursday"},
                            {"value": "fri", "label": "Friday"},
                            {"value": "sat", "label": "Saturday"},
                            {"value": "sun", "label": "Sunday"},
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("evening_exclude_holidays", default=True): bool,
                vol.Optional("evening_custom_exclude_dates"): str,
                vol.Optional(CONF_NOTIFY, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="notify", multiple=True)
                ),
            }),
            errors=errors,
        )

    async def async_step_finish(self, user_input=None):
        """Finish configuration."""
        if not self.people:
            return self.async_abort(reason="no_people")

        return self.async_create_entry(
            title="Family Transport Tracker",
            data={
                "people": self.people,
                "station_radius": DEFAULT_STATION_RADIUS,
                "route_tolerance": DEFAULT_ROUTE_TOLERANCE,
                "departure_window": DEFAULT_DEPARTURE_WINDOW,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return FamilyTransportTrackerOptionsFlow(config_entry)


class FamilyTransportTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry
        self.people = list(config_entry.data.get("people", []))
        self.current_person_index = None

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "edit_person":
                return await self.async_step_select_person()
            elif action == "settings":
                return await self.async_step_settings()
        
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_person", "settings"],
        )
    
    async def async_step_select_person(self, user_input=None):
        """Select which person to edit."""
        if not self.people:
            # No people configured yet
            return self.async_abort(reason="no_people_configured")
        
        if user_input is not None:
            self.current_person_index = user_input["person_index"]
            return await self.async_step_edit_person()
        
        person_options = []
        for i, p in enumerate(self.people):
            entity_id = p.get("person", f"Person {i+1}")
            # Get friendly name from entity_id (e.g., device_tracker.life360_john -> John)
            name = entity_id.split(".")[-1].replace("life360_", "").replace("_", " ").title()
            person_options.append({"value": str(i), "label": name})
        
        return self.async_show_form(
            step_id="select_person",
            data_schema=vol.Schema({
                vol.Required("person_index"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=person_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )
    
    async def async_step_edit_person(self, user_input=None):
        """Edit a person's configuration."""
        try:
            if user_input is not None:
                idx = int(self.current_person_index)
                self.people[idx] = user_input
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        **self._config_entry.data,
                        "people": self.people,
                    },
                )
                return self.async_create_entry(title="", data={})
            
            idx = int(self.current_person_index)
            person = self.people[idx]
            
            _LOGGER.debug("Editing person %s with data: %s", idx, person)
            
            return self.async_show_form(
                step_id="edit_person",
                data_schema=vol.Schema({
                    vol.Required(CONF_PERSON, default=person.get(CONF_PERSON)): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="device_tracker")
                    ),
                    vol.Optional(CONF_MORNING_ROUTE, default=person.get(CONF_MORNING_ROUTE)): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional("morning_departure_time", default=person.get("morning_departure_time")): selector.TimeSelector(),
                    vol.Optional("morning_days", default=person.get("morning_days", ["mon", "tue", "wed", "thu", "fri"])): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "mon", "label": "Monday"},
                                {"value": "tue", "label": "Tuesday"},
                                {"value": "wed", "label": "Wednesday"},
                                {"value": "thu", "label": "Thursday"},
                                {"value": "fri", "label": "Friday"},
                                {"value": "sat", "label": "Saturday"},
                                {"value": "sun", "label": "Sunday"},
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("morning_exclude_holidays", default=person.get("morning_exclude_holidays", True)): bool,
                    vol.Optional("morning_custom_exclude_dates", default=person.get("morning_custom_exclude_dates", "")): str,
                    vol.Optional(CONF_EVENING_ROUTE, default=person.get(CONF_EVENING_ROUTE)): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional("evening_departure_time", default=person.get("evening_departure_time")): selector.TimeSelector(),
                    vol.Optional("evening_days", default=person.get("evening_days", ["mon", "tue", "wed", "thu", "fri"])): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": "mon", "label": "Monday"},
                                {"value": "tue", "label": "Tuesday"},
                                {"value": "wed", "label": "Wednesday"},
                                {"value": "thu", "label": "Thursday"},
                                {"value": "fri", "label": "Friday"},
                                {"value": "sat", "label": "Saturday"},
                                {"value": "sun", "label": "Sunday"},
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("evening_exclude_holidays", default=person.get("evening_exclude_holidays", True)): bool,
                    vol.Optional("evening_custom_exclude_dates", default=person.get("evening_custom_exclude_dates", "")): str,
                    vol.Optional(CONF_NOTIFY, default=person.get(CONF_NOTIFY, [])): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="notify", multiple=True)
                    ),
                }),
            )
        except Exception as err:
            _LOGGER.error("Error in async_step_edit_person: %s", err, exc_info=True)
            return self.async_abort(reason="edit_person_error")

    async def async_step_settings(self, user_input=None):
        """Manage the settings."""
        if user_input is not None:
            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data={
                    **self._config_entry.data,
                    **user_input,
                },
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_STATION_RADIUS,
                    default=self._config_entry.data.get("station_radius", DEFAULT_STATION_RADIUS),
                ): int,
                vol.Optional(
                    CONF_ROUTE_TOLERANCE,
                    default=self._config_entry.data.get("route_tolerance", DEFAULT_ROUTE_TOLERANCE),
                ): int,
                vol.Optional(
                    CONF_DEPARTURE_WINDOW,
                    default=self._config_entry.data.get("departure_window", DEFAULT_DEPARTURE_WINDOW),
                ): int,
            }),
        )

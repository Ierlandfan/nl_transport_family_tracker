"""Config flow for Family Transport Tracker."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_STATION_RADIUS,
                    default=self.config_entry.data.get("station_radius", DEFAULT_STATION_RADIUS),
                ): int,
                vol.Optional(
                    CONF_ROUTE_TOLERANCE,
                    default=self.config_entry.data.get("route_tolerance", DEFAULT_ROUTE_TOLERANCE),
                ): int,
                vol.Optional(
                    CONF_DEPARTURE_WINDOW,
                    default=self.config_entry.data.get("departure_window", DEFAULT_DEPARTURE_WINDOW),
                ): int,
            }),
        )

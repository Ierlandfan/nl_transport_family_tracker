"""Constants for Family Transport Tracker."""

DOMAIN = "transport_family_tracker"

CONF_PERSON = "person"
CONF_MORNING_ROUTE = "morning_route"
CONF_EVENING_ROUTE = "evening_route"
CONF_NOTIFY = "notify_entities"
CONF_STATION_RADIUS = "station_radius"
CONF_ROUTE_TOLERANCE = "route_tolerance"
CONF_DEPARTURE_WINDOW = "departure_window"

DEFAULT_STATION_RADIUS = 100  # meters
DEFAULT_ROUTE_TOLERANCE = 500  # meters
DEFAULT_DEPARTURE_WINDOW = 5  # minutes

STATUS_ON_ROUTE = "On Route"
STATUS_MISSED = "Missed"
STATUS_DELAYED = "Delayed"
STATUS_ALTERNATIVE = "Alternative Route"
STATUS_NOT_TRAVELING = "Not Traveling"
STATUS_AT_STATION = "At Station"
STATUS_BY_CAR = "By Car"
STATUS_STOPPED = "Stopped"
STATUS_DETOURED = "Detoured"

ATTR_PLANNED_ROUTE = "planned_route"
ATTR_CURRENT_LOCATION = "current_location"
ATTR_DEPARTURE_TIME = "departure_time"
ATTR_EXPECTED_ARRIVAL = "expected_arrival"
ATTR_DELAY_MINUTES = "delay_minutes"
ATTR_ALTERNATIVE_AVAILABLE = "alternative_available"
ATTR_CONFIDENCE = "confidence"
ATTR_NEXT_STATION = "next_station"
ATTR_TRAVEL_MODE = "travel_mode"
ATTR_CAR_ETA = "car_eta"
ATTR_STOP_ADDRESS = "stop_address"
ATTR_STOP_DURATION = "stop_duration"
ATTR_DETOUR_LOCATION = "detour_location"
ATTR_LEFT_ON_TIME = "left_on_time"
ATTR_DRIVING_SPEED = "driving_speed"

SPEED_THRESHOLD_DRIVING = 30  # km/h - above this is considered driving
SPEED_THRESHOLD_STOPPED = 5  # km/h - below this is considered stopped

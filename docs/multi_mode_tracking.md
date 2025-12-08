# Multi-Modal Journey Tracking

This guide explains how to set up intelligent tracking that automatically detects whether family members are using public transport, driving, or making unexpected stops.

## Overview

The multi-modal tracking system combines:
- **Life360** - Real-time GPS location
- **Waze Travel Time** - Car journey ETAs
- **Dutch Transport Sensors** - Expected departure times
- **Template Sensors** - Smart logic to determine transport mode

## Prerequisites

### 1. Install Life360 Integration

```bash
# Via HACS
1. Open HACS → Integrations
2. Search for "Life360"
3. Install pnbruckner/ha-life360
4. Restart Home Assistant
```

Configure Life360:
```yaml
# configuration.yaml
life360:
  accounts:
    - username: !secret life360_username
      password: !secret life360_password
```

### 2. Install Waze Travel Time

Already built into Home Assistant!

```yaml
# configuration.yaml
waze_travel_time:
  - name: "John to Work"
    origin: device_tracker.john_life360
    destination: zone.work
    region: 'EU'

  - name: "John to Home"
    origin: device_tracker.john_life360
    destination: zone.home
    region: 'EU'
```

### 3. Define Zones

```yaml
# configuration.yaml
zone:
  - name: Bus Stop Leidschenveen
    latitude: 52.0644
    longitude: 4.3959
    radius: 100
    icon: mdi:bus-stop

  - name: Den Haag Centraal
    latitude: 52.0808
    longitude: 4.3250
    radius: 200
    icon: mdi:train-car

  - name: Work
    latitude: 52.3676
    longitude: 4.9041
    radius: 100
    icon: mdi:briefcase
```

## Core Template Sensors

### 1. Journey Status Sensor

Detects what stage of the journey the person is at:

```yaml
template:
  - sensor:
      - name: "John Journey Status"
        unique_id: john_journey_status
        state: >
          {% set person = 'device_tracker.john_life360' %}
          {% set speed = state_attr(person, 'speed') | float(0) %}
          {% set bus_stop = 'zone.bus_stop_leidschenveen' %}
          {% set station = 'zone.den_haag_centraal' %}
          
          {# Calculate distances #}
          {% set dist_to_bus = distance(person, bus_stop) %}
          {% set dist_to_station = distance(person, station) %}
          
          {# Get next bus departure time #}
          {% set bus_departs = state_attr('sensor.morning_bus', 'minutes_until_departure') | int %}
          {% set bus_departed = bus_departs < -5 %}
          
          {# Determine status #}
          {% if is_state('person.john', 'home') %}
            home
          {% elif dist_to_bus < 0.1 and speed < 5 %}
            waiting_at_stop
          {% elif speed > 10 and speed < 60 and not bus_departed %}
            on_bus
          {% elif dist_to_station < 0.2 and speed < 5 %}
            at_transfer
          {% elif speed > 60 and speed < 140 %}
            on_train
          {% elif bus_departed and dist_to_bus > 0.5 and speed < 5 %}
            missed_bus
          {% elif speed > 5 and speed < 10 %}
            walking
          {% elif is_state('person.john', 'work') %}
            arrived
          {% else %}
            unknown
          {% endif %}

        attributes:
          distance_to_bus_stop: >
            {{ distance('device_tracker.john_life360', 'zone.bus_stop_leidschenveen') | round(2) }}
          distance_to_station: >
            {{ distance('device_tracker.john_life360', 'zone.den_haag_centraal') | round(2) }}
          current_speed: >
            {{ state_attr('device_tracker.john_life360', 'speed') | float(0) | round(1) }}
```

### 2. Transport Mode Detector

```yaml
template:
  - sensor:
      - name: "John Transport Mode"
        unique_id: john_transport_mode
        state: >
          {% set speed = state_attr('device_tracker.john_life360', 'speed') | float(0) %}
          {% set journey_status = states('sensor.john_journey_status') %}
          
          {% if speed < 5 %}
            stationary
          {% elif speed < 10 %}
            walking
          {% elif journey_status == 'on_bus' %}
            bus
          {% elif journey_status == 'on_train' %}
            train
          {% elif speed > 60 %}
            car
          {% else %}
            unknown
          {% endif %}

        icon: >
          {% set mode = states('sensor.john_transport_mode') %}
          {% if mode == 'bus' %}
            mdi:bus
          {% elif mode == 'train' %}
            mdi:train
          {% elif mode == 'car' %}
            mdi:car
          {% elif mode == 'walking' %}
            mdi:walk
          {% else %}
            mdi:help-circle
          {% endif %}
```

### 3. Unexpected Stop Detector

```yaml
template:
  - binary_sensor:
      - name: "John Unexpected Stop"
        unique_id: john_unexpected_stop
        state: >
          {% set status = states('sensor.john_journey_status') %}
          {% set mode = states('sensor.john_transport_mode') %}
          {% set speed = state_attr('device_tracker.john_life360', 'speed') | float(0) %}
          
          {# Person should be moving but is stationary for >5 min #}
          {% set commute_active = is_state('binary_sensor.john_commute_hours', 'on') %}
          {% set not_at_known_location = states('person.john') == 'not_home' %}
          
          {{ commute_active and not_at_known_location and speed < 5 and 
             status not in ['waiting_at_stop', 'at_transfer', 'home', 'arrived'] }}

        attributes:
          duration: >
            {{ relative_time(states.binary_sensor.john_unexpected_stop.last_changed) }}
          location: >
            {{ state_attr('device_tracker.john_life360', 'address') }}
```

### 4. Stop Duration Tracker

```yaml
template:
  - sensor:
      - name: "John Stop Duration"
        unique_id: john_stop_duration
        state: >
          {% if is_state('binary_sensor.john_unexpected_stop', 'on') %}
            {{ ((as_timestamp(now()) - as_timestamp(states.binary_sensor.john_unexpected_stop.last_changed)) / 60) | round(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "min"
```

## Automations

### 1. Auto-Detect Transport Mode on Departure

```yaml
automation:
  - alias: "Detect John's Transport Mode"
    trigger:
      - platform: state
        entity_id: person.john
        from: "home"
    action:
      # Force location update
      - service: life360.update_location
        target:
          entity_id: device_tracker.john_life360
      
      # Wait for location to update
      - delay: "00:00:10"
      
      # Determine mode and notify
      - choose:
          # Driving detected
          - conditions:
              - condition: template
                value_template: >
                  {{ state_attr('device_tracker.john_life360', 'speed') | float(0) > 40 }}
            sequence:
              - service: notify.family
                data:
                  message: "John is driving to work. ETA: {{ states('sensor.john_to_work') }}"

          # At bus stop
          - conditions:
              - condition: template
                value_template: >
                  {{ distance('device_tracker.john_life360', 'zone.bus_stop_leidschenveen') < 0.1 }}
            sequence:
              - service: notify.family
                data:
                  message: >
                    John is at the bus stop. 
                    Next bus: {{ state_attr('sensor.morning_bus', 'minutes_until_departure') }} min
```

### 2. Monitor for Missed Transport

```yaml
automation:
  - alias: "Alert Missed Bus"
    trigger:
      - platform: state
        entity_id: sensor.john_journey_status
        to: "missed_bus"
    action:
      - service: notify.mobile_app_johns_phone
        data:
          title: "🚌 Missed Bus"
          message: >
            You missed the {{ state_attr('sensor.morning_bus', 'line_number') }}. 
            Next options:
            - {{ state_attr('sensor.morning_bus_1', 'expected_departure_time') }} 
            - {{ state_attr('sensor.morning_bus_2', 'expected_departure_time') }}
          data:
            priority: high
            ttl: 0

      - service: notify.family
        data:
          message: "John missed the bus. Next departure in {{ state_attr('sensor.morning_bus_1', 'minutes_until_departure') }} min"
```

### 3. Unexpected Stop Alert

```yaml
automation:
  - alias: "Unexpected Stop Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.john_unexpected_stop
        to: "on"
        for:
          minutes: 5
    action:
      - service: notify.family
        data:
          title: "📍 Unexpected Stop"
          message: >
            John stopped at {{ state_attr('device_tracker.john_life360', 'address') }}
            for {{ states('sensor.john_stop_duration') }} minutes
          data:
            actions:
              - action: "CALL_JOHN"
                title: "Call"
              - action: "VIEW_MAP"
                title: "Map"
```

### 4. Journey Resumed After Stop

```yaml
automation:
  - alias: "Journey Resumed"
    trigger:
      - platform: state
        entity_id: binary_sensor.john_unexpected_stop
        from: "on"
        to: "off"
    action:
      - service: notify.family
        data:
          message: >
            John is moving again ({{ states('sensor.john_transport_mode') }}).
            {% if is_state('sensor.john_transport_mode', 'car') %}
            New ETA: {{ states('sensor.john_to_work') }}
            {% else %}
            Next stop: {{ state_attr('sensor.morning_bus', 'destination') }}
            {% endif %}
```

### 5. Car ETA Updates

```yaml
automation:
  - alias: "Update Car ETA"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    condition:
      - condition: state
        entity_id: sensor.john_transport_mode
        state: "car"
      - condition: state
        entity_id: person.john
        state: "not_home"
    action:
      - service: homeassistant.update_entity
        target:
          entity_id: sensor.john_to_work
```

## Binary Sensors for Journey Stages

```yaml
template:
  - binary_sensor:
      - name: "John At Bus Stop"
        state: >
          {{ distance('device_tracker.john_life360', 'zone.bus_stop_leidschenveen') < 0.1 }}

      - name: "John On Bus"
        state: >
          {{ is_state('sensor.john_journey_status', 'on_bus') }}

      - name: "John At Station"
        state: >
          {{ distance('device_tracker.john_life360', 'zone.den_haag_centraal') < 0.2 }}

      - name: "John On Train"
        state: >
          {{ is_state('sensor.john_journey_status', 'on_train') }}

      - name: "John Commute Active"
        state: >
          {{ states('sensor.john_journey_status') not in ['home', 'arrived', 'unknown'] }}
```

## Location Update Optimization

To balance accuracy with battery life:

```yaml
automation:
  - alias: "Frequent Updates During Commute"
    trigger:
      - platform: state
        entity_id: binary_sensor.john_commute_active
        to: "on"
    action:
      - repeat:
          while:
            - condition: state
              entity_id: binary_sensor.john_commute_active
              state: "on"
          sequence:
            - service: life360.update_location
              target:
                entity_id: device_tracker.john_life360
            - delay: "00:02:00"  # Update every 2 minutes during commute
```

## Testing

1. **Test at home:**
   - Journey status should be `home`
   - Transport mode should be `stationary`

2. **Test leaving home:**
   - Walk to bus stop
   - Status should change to `waiting_at_stop`

3. **Test on bus:**
   - Mode should change to `bus`
   - Status should be `on_bus`

4. **Test car journey:**
   - Drive instead of taking bus
   - Mode should detect `car`
   - No missed bus alerts

5. **Test unexpected stop:**
   - Stop at gas station during commute
   - Alert should trigger after 5 minutes

## Troubleshooting

### Location not updating
- Check Life360 app permissions
- Verify location services enabled
- Manually trigger: `life360.update_location`

### Inaccurate speed readings
- GPS accuracy might be low
- Add minimum accuracy filter in templates
- Increase detection thresholds

### False missed bus alerts
- Adjust time threshold (`-5` minutes)
- Increase distance threshold (`0.5` km)

---

**Next Steps:**
- [Example Dashboard](../examples/dashboard.yaml)
- [Example Automations](../examples/automations.yaml)
- [Contributing Guide](../CONTRIBUTING.md)

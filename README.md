# 🚂👨‍👩‍👧 Family Transport Tracker

A Home Assistant integration that tracks if family members are on their planned public transport routes by combining:
- **Life360** location data
- **Dutch Public Transport** schedule data
- **Smart proximity detection** to determine if they're on the right train/bus
- **Automatic notifications** for missed transport or route deviations

## Features

✅ **Automatic Route Detection**
- Links Life360 family members to transport routes
- Detects if they're at the departure station
- Checks if they boarded the planned transport
- Tracks journey progress

✅ **Smart Notifications**
- Alert if family member misses their usual train/bus
- Notify if they're delayed at departure
- Suggest alternative routes when needed
- Send ETA updates to other family members

✅ **Schedule Learning**
- Learns typical commute patterns
- Auto-assigns routes based on time of day
- Adapts to weekday/weekend schedules
- Detects irregular trips

✅ **Family Coordination**
- "Where is Dad?" - See if he's on the train home
- Shared arrival ETAs
- Pickup coordination at destination
- Group journey tracking

✅ **Alternative Route Suggestions**
- Real-time alternative options when transport is missed
- Fastest route calculations
- Notify about delays/cancellations
- Walking/taxi time estimates

## How It Works

### 1. Setup Person-Route Mapping
```yaml
# Via UI configuration:
Person: "Dad"
Usual Morning Route: Amsterdam → Utrecht (08:30 departure)
Usual Evening Route: Utrecht → Amsterdam (17:45 departure)
Notification Recipients: ["Mom", "Kids"]
```

### 2. Automatic Detection

The integration monitors:
- **At Station** - Is person within 100m of departure station?
- **Departed On Time** - Did they leave station on schedule?
- **En Route** - Moving along expected route path?
- **Arrived** - Reached destination zone?
- **Missed** - Still at station after departure time?

### 3. Status Tracking

Creates sensors:
- `sensor.dad_transport_status`
  - States: "On Route", "Missed", "Alternative Route", "Not Traveling", "Delayed"
- `sensor.dad_current_eta`
  - Estimated arrival time
- `binary_sensor.dad_on_planned_route`
  - True/False

### 4. Notifications

Automatic alerts:
```
🚂 Dad missed the 08:30 train to Utrecht
⏰ Next train: 08:45 (Platform 7b)
⚡ Alternative: Express 08:40 (Platform 3) - 5 min faster
```

```
✅ Dad is on the 17:45 train home
📍 Currently passing: Breukelen
🏠 ETA: 18:32 (On Time)
```

```
⚠️ Dad's train delayed 10 minutes
🏠 New ETA: 18:42
Reason: Technical issues
```

## Configuration

### Person Configuration
- Select Life360 device tracker
- Assign usual routes (morning/evening)
- Set notification preferences
- Configure time windows

### Route Proximity Settings
- Station radius (default: 100m)
- En-route tolerance (default: 500m)
- Departure window (default: 5 min before/after)

### Notification Settings
- Who to notify
- Notification types (missed, delayed, arrived)
- Quiet hours
- Priority levels

## Use Cases

### 1. Parent Commute Tracking
**Scenario**: Mom wants to know when Dad's train is delayed
- Integration detects Dad at station
- Checks if train is delayed
- Sends notification to Mom with new ETA
- Updates when Dad boards alternate route

### 2. Kid School Commute
**Scenario**: Track if teenager catches morning bus
- Detects proximity to bus stop at 07:50
- Confirms departure at 08:00
- Sends "On the bus" notification to parents
- Alerts if missed + shows next bus time

### 3. Pickup Coordination
**Scenario**: Pick up partner at station
- Monitors partner's train status
- Sends ETA updates
- Notifies when train arrives
- Accounts for delays automatically

### 4. Emergency Alerts
**Scenario**: Family member stuck at station
- Detects person still at station 15 min after departure
- Checks for service disruptions
- Suggests alternatives
- Notifies family immediately

## Sensors Created

### Per Person
```
sensor.{person}_transport_status
  State: On Route | Missed | Delayed | Alternative | Not Traveling
  Attributes:
    - planned_route
    - current_location
    - departure_time
    - expected_arrival
    - actual_arrival
    - delay_minutes
    - alternative_available

sensor.{person}_transport_eta
  State: Time (e.g., "18:32")
  Attributes:
    - original_eta
    - delay
    - distance_remaining
    - next_station

binary_sensor.{person}_on_planned_route
  State: True/False
  Attributes:
    - route_matched
    - confidence
    - last_check

sensor.{person}_alternative_routes
  State: Number of alternatives
  Attributes:
    - routes (list of alternative options)
    - fastest_alternative
    - next_departure
```

## Automations Enabled

### Example 1: Missed Train Alert
```yaml
automation:
  - alias: "Dad Missed Train"
    trigger:
      platform: state
      entity_id: sensor.dad_transport_status
      to: "Missed"
    action:
      - service: notify.mobile_app_mom
        data:
          title: "🚂 Train Missed"
          message: >
            Dad missed the {{ state_attr('sensor.dad_transport_status', 'planned_route') }}.
            Next train: {{ state_attr('sensor.dad_alternative_routes', 'next_departure') }}
```

### Example 2: Arrival Notification
```yaml
automation:
  - alias: "Dad Almost Home"
    trigger:
      platform: numeric_state
      entity_id: sensor.dad_transport_eta
      below: 10  # minutes
    action:
      - service: notify.family
        data:
          message: "Dad's train arrives in {{ states('sensor.dad_transport_eta') }} minutes!"
```

### Example 3: Delay Alert
```yaml
automation:
  - alias: "Train Delayed"
    trigger:
      platform: state
      entity_id: sensor.dad_transport_status
      to: "Delayed"
    condition:
      - condition: numeric_state
        entity_id: sensor.dad_transport_eta
        attribute: delay_minutes
        above: 5
    action:
      - service: notify.mobile_app_mom
        data:
          title: "⚠️ Train Delayed"
          message: >
            Dad's train delayed {{ state_attr('sensor.dad_transport_eta', 'delay_minutes') }} minutes.
            New arrival: {{ states('sensor.dad_transport_eta') }}
```

## Dashboard Cards

### Status Card
```yaml
type: entities
title: Family Transport Status
entities:
  - entity: sensor.dad_transport_status
    name: Dad
    icon: mdi:train
  - entity: sensor.mom_transport_status
    name: Mom
    icon: mdi:bus
  - entity: sensor.kid_transport_status
    name: Sarah
    icon: mdi:school-bus
```

### Journey Map
```yaml
type: map
title: Family Journeys
entities:
  - device_tracker.life360_dad
  - device_tracker.route_amsterdam_centraal_to_utrecht_centraal
auto_fit: true
```

### ETA Card
```yaml
type: glance
title: Arrival Times
entities:
  - entity: sensor.dad_transport_eta
    name: Dad
  - entity: sensor.mom_transport_eta
    name: Mom
columns: 2
```

## Installation

### Prerequisites
1. **Life360 Integration** - Must be configured with family members
2. **Dutch Public Transport Integration** - Routes must be set up
3. **Home Assistant Zones** - Home, Work, etc. defined

### Install via HACS
1. Add custom repository: `https://github.com/yourusername/nl_transport_family_tracker`
2. Install "Family Transport Tracker"
3. Restart Home Assistant
4. Configure via UI

### Configuration Steps
1. Settings → Integrations → Add Integration
2. Search "Family Transport Tracker"
3. Select family members (Life360 entities)
4. Assign their usual routes
5. Configure notifications
6. Done!

## Smart Features

### Pattern Learning
- Learns when family members typically travel
- Auto-detects routine vs one-off trips
- Adjusts expectations for weekends/holidays
- Recognizes commute patterns

### Confidence Scoring
- GPS accuracy-based confidence
- Multiple data point validation
- Ignores spurious location updates
- "High confidence" vs "Low confidence" alerts

### Multi-Modal Detection
- Handles train → bus transfers
- Tracks walking between stations
- Detects taxi/car alternatives
- Monitors entire door-to-door journey

### Battery Awareness
- Reduces check frequency on low battery
- Caches last known status
- Notifies if device offline during commute

## Advanced Options

### Geofencing
- Custom station boundaries
- Route corridor definition
- Transfer point detection
- Arrival zone radius

### Time Windows
- Departure time flexibility (±5 min default)
- Rush hour vs off-peak detection
- Schedule variations (express trains)

### Privacy
- Data stays local (no cloud)
- Optional sharing controls
- Notification opt-in/out
- Location history retention

## Technical Details

### Update Frequency
- **At station**: Every 30 seconds
- **En route**: Every 60 seconds
- **Not traveling**: Every 5 minutes

### Data Sources
- Life360 device tracker (GPS)
- Dutch Public Transport (schedules)
- Home Assistant zones
- Historical journey data

### Requirements
- Home Assistant 2024.8+
- Life360 integration
- Dutch Public Transport integration
- Internet connection

## Troubleshooting

### False "Missed" Alerts
- Increase departure time window
- Adjust station proximity radius
- Check GPS accuracy settings

### No Notifications
- Verify notification service configured
- Check quiet hours settings
- Ensure recipients selected

### Wrong Route Detection
- Review person-route mapping
- Check time window configuration
- Verify Life360 updates working

## Future Enhancements

- Machine learning for route prediction
- Traffic delay correlation
- Weather-based suggestions
- Carbon footprint tracking
- Cost tracking per journey
- Social features (share ETA with friends)

---

**Keep your family connected and never miss a train again!** 🚂👨‍👩‍👧

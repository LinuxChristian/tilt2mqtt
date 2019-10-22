
# Tilt2MQTT - Stream the Tilt Hydrometer to MQTT

*Note* This package requires a MQTT server. To get one read [here](https://philhawthorne.com/setting-up-a-local-mosquitto-server-using-docker-for-mqtt-communication/).

Wrapper for reading messages from Tilt hydrometer and sending them via MQTT

This script listen for messages from the Tilt hydrometer via bluetooth.
The devices act as a simple IBeacon sending the following two values,

 * major: Temperature in Farenheit
 * minor: Specific gravity

The script works a follows,

 * Listen for Tilt devices filtered by the TILTS global variable
 * If found the callback is triggered
  * Translate the UUID to a Tilt color
  * Extract and convert measurements from the device
  * Construct a JSON payload
  * Send payload to the MQTT server
 * Stop listening and sleep for X minutes before getting a new measurement

# How to run

First install Python dependencies

```
pip install beacontools paho-mqtt requests
```

Run the script,

```
python tilt2mqtt.py
```

The code should now listen for your Tilt device and report values on the MQTT topic that matches your Tilt color.

You can use the mosquitto commandline tool to listen for messages,

```bash
mosquitto_sub -t '#'
```

To listen on all colors or,

```bash
mosquitto_sub -t '<YOUR COLOR>/#'
```

To set specific MQTT settings use the following environmental variables,

| Varable name | Default value | 
|--------------|---------------+
| MQTT_IP      |     127.0.0.1 |
| MQTT_PORT    |          1883 |
| MQTT_AUTH    |          NONE |
| MQTT_DEBUG   |    TRUE       |

# Using tilt2MQTT with Home assistant

Using the MQTT sensor in home assistant you can how listen for new values and create automations rules based on the values (e.g. start a heater if the temperature is too low).

```yanl
  - platform: mqtt
    name: "Tilt Orange - Temperature"
    state_topic: "tilt/Orange"
    value_template: "{{ value_json.temperature_celsius_uncali | float + 0.5 | float | round(2) }}"
    unit_of_measurement: "\u2103"

  - platform: mqtt
    name: "Tilt Orange - Gravity"
    state_topic: "tilt/Orange"
    value_template: "{{ value_json.specific_gravity_uncali | float + 0.002 | float | round(3) }}"
```

Notice that here the calibration value is added directly to the value template in home assistant.

# Using with Brewers friend

Using the following [gist](https://gist.github.com/LinuxChristian/c00486eaee5a55daa790122ac4236c11) it is possible to stream the calibrated values from home assistant to the brewers friend API via a simple Python script.

# Note

The values reported by the Tilt are uncalibrated so you must calibrate values before use.

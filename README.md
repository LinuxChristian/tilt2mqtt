
# Tilt2MQTT - Stream the Tilt Hydrometer to MQTT

##### Table of Contents
1. [Inroduction](#intro)
2. [How to run](#howtorun)
3. [Running as a service](#runasservice)
4. [Integrate with Home Assistant](#intwithhass)
5. [Integrate with Brewers Friend](#brewers)

<a name="intro"/>

# Introduction

**Note:** This package requires a MQTT server. To get one read [here](https://philhawthorne.com/setting-up-a-local-mosquitto-server-using-docker-for-mqtt-communication/).

Wrapper for reading messages from [Tilt wireless hydrometer](https://tilthydrometer.com/) and forwarding them to MQTT topics. 

The device acts as a simple Bluetooth IBeacon sending the following two values,

 * major: Temperature in Farenheit
 * minor: Specific gravity

The raw values read from the Tilt are uncalibrated and should be calibrated before use. The script works a follows,

 1. Listen for local IBeacon devices
 2. If found the callback is triggered
  * Translate the UUID to a Tilt color
  * Extract and convert measurements from the device
  * Construct a JSON payload
  * Send payload to the MQTT server
 3. Stop listening and sleep for X minutes before getting a new measurement

This script has been tested on Linux. By default the script will create a log file in the path `/tmp/tilt.log`.

<a name="howtorun"/>

# How to run

If you are on Linux first install the bluetooth packages,

```bash
sudo apt-get install libbluetooth-dev
```

Then install Python dependencies

```
pip install beacontools paho-mqtt requests pybluez
```

Run the script,

```
python tilt2mqtt.py
```

**Note**: If you get a permission error try running the script as root.

The code should now listen for your Tilt device and report values on the MQTT topic that matches your Tilt color.

You can use the mosquitto commandline tool (on Linux) to listen for colors or the build-in MQTT client in Home Assistant,

```bash
mosquitto_sub -t 'tilt/#'
```

To listen for measurements only from Orange devices run,

```bash
mosquitto_sub -t 'tilt/Orange/#'
```

If your MQTT server is not running on the localhost you can set the following environmental variables,

| Varable name | Default value 
|--------------|---------------
| MQTT_IP      |     127.0.0.1
| MQTT_PORT    |          1883
| MQTT_AUTH    |          NONE
| MQTT_DEBUG   |    TRUE      

<a name="runasservice"/>

# Running tilt2MQTT as a service on Linux

If you would like to run tilt2MQTT as a service on Linux using systemd add this file to a systemd path (Normally /lib/systemd/system/tilt2mqtt.service or /etc/systemd/system/tilt2mqtt.service)

```bash
# On debian Linux add this file to /lib/systemd/system/tilt2mqtt.service

[Unit]
Description=Tilt Hydrometer Service
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 <PATH TO YOUR FILE>/tilt2mqtt.py
StandardInput=tty-force

[Install]
WantedBy=multi-user.target
```

Remember to change the PATH variable in the script above. Then update your service,

```
sudo systemctl reload-daemon
```

<a name="intwithhass"/>

# Using tilt2MQTT with Home assistant

Using the MQTT sensor in home assistant you can now listen for new values and create automations rules based on the values (e.g. start a heater if the temperature is too low).

```yaml
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

Notice that here the calibration value is added directly to the value template in home assistant. The calibration parameters are estimated following the [Tilt guide](https://tilthydrometer.com/blogs/news/adding-calibration-points-within-your-tilt-app).

![Home Assistant - Brewing](http://fredborg-braedstrup.dk/images/HomeAssistant-brewing.png)

<a name="brewers"/>

# Using with Brewers friend

Using the following [gist](https://gist.github.com/LinuxChristian/c00486eaee5a55daa790122ac4236c11) it is possible to stream the calibrated values from home assistant to the brewers friend API via a simple Python script. After this you can add the tilt2mqtt.service to 

![Brewers Friend fermentation overview](http://fredborg-braedstrup.dk/images/BrewersFriend-fermentation.png)

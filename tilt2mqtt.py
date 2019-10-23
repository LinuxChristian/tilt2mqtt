#!/usr/bin/env python
"""
Wrapper for reading messages from Tilt wireless hydrometer and forwarding them to MQTT topics. 

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

This script has been tested on Linux.

# How to run

First install Python dependencies

 pip install beacontools paho-mqtt requests

Run the script,

 python tilt2mqtt.py

Note: A MQTT server is required.
"""

import time
import logging as lg
import os
import json
from beacontools import BeaconScanner, IBeaconFilter, parse_packet, const
import paho.mqtt.publish as publish
import requests

#
# Constants
#
sleep_interval = 60*30  # How often to listen for new messages in seconds

lg.basicConfig(level=lg.INFO)
LOG = lg.getLogger()

# Create handlers
c_handler = lg.StreamHandler()
f_handler = lg.FileHandler('/tmp/tilt.log')
c_handler.setLevel(lg.DEBUG)
f_handler.setLevel(lg.INFO)

# Create formatters and add it to handlers
c_format = lg.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
LOG.addHandler(c_handler)
LOG.addHandler(f_handler)

# Unique bluetooth IDs for Tilt sensors
TILTS = {
        'a495bb10c5b14b44b5121370f02d74de': 'Red',
        'a495bb20c5b14b44b5121370f02d74de': 'Green',
        'a495bb30c5b14b44b5121370f02d74de': 'Black',
        'a495bb40c5b14b44b5121370f02d74de': 'Purple',
        'a495bb50c5b14b44b5121370f02d74de': 'Orange',
        'a495bb60c5b14b44b5121370f02d74de': 'Blue',
        'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
        'a495bb80c5b14b44b5121370f02d74de': 'Pink',
}

# MQTT Settings
config = {
        'host': os.getenv('MQTT_IP', '127.0.0.1'),
        'port':int(os.getenv('MQTT_PORT', 1883)),
        'auth':os.getenv('MQTT_AUTH', None),
        'debug': os.getenv('MQTT_DEBUG', True),
}

def callback(bt_addr, rssi, packet, additional_info):
    """Message recieved from tilt
    """
    LOG.info(additional_info)
    msgs = []
    color = "unknown"

    try:
        uuid = additional_info["uuid"]
        color = TILTS[uuid.replace('-','')]
    except KeyError:
        LOG.error("Unable to decode tilt color. Additional info was {}".format(additional_info))

    try:
        # Get and convert temperature
        temperature_farenheit = float(additional_info["major"])
        temperature_celsius = (temperature_farenheit - 32) * 5/9

        # Get and convert gravity
        specific_gravity = float(additional_info["minor"])/1000
        degree_plato = 135.997*pow(specific_gravity, 3) - 630.272*pow(specific_gravity, 2) + 1111.14*specific_gravity - 616.868

        data = {
            "specific_gravity_uncali": "{:.3f}".format(specific_gravity),
            "plato_uncali": "{:.2f}".format(degree_plato),
            "temperature_celsius_uncali": "{:.2f}".format(temperature_celsius),
            "temperature_farenheit_uncali": "{:.1f}".format(temperature_farenheit)
        }

        # Create message                                        QoS   Retain message
        msgs.append(("tilt/{}".format(color), json.dumps(data), 2,    1))

        # Send message via MQTT server
        publish.multiple(msgs, hostname=config['host'], port=config['port'], auth=config['auth'], protocol=4)
    except KeyError:
        LOG.error("Device does not look like a Tilt Hydrometer.")

scanner = BeaconScanner(callback)

scanner.start()
monitor = scanner._mon
while(1):
    LOG.info("Started scanning")
    # Start scanning in active mode
    monitor.toggle_scan(True)

    # Time to wait for tilt to respond
    time.sleep(5)

    LOG.info("Stopped scanning")
    # Stop again
    monitor.toggle_scan(False)

    # Wait until next scan periode
    time.sleep(sleep_interval)

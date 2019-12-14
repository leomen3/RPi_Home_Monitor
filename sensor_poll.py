#!/usr/bin/env python
 ###########################################################################
# 1) poll temperature and humidity from DHT11
# 2) send samples to the MQTT broker
###########################################################################

import paho.mqtt.client as mqtt
import Adafruit_DHT
import time

RPi_HOST = "10.0.0.18"
localBroker = RPi_HOST		# Local MQTT broker
localPort = 1883			# Local MQTT port

#Define MQTT topics:
TEMPERATURE_CHIPA = "/sensor/Chipa/temperature"
HUMIDITY_CHIPA = "/sensor/Chipa/humidity"
SAMPLE_DELAY = 5 ##sample every 5 seconds
localTimeOut = 120


def on_connect(client, userdata, flags, rc):
    #MQTT configs
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")

def on_message(client, userdata, msg):
    print("Test recieved")
    return

#Humidity and temperature sensor
sensor = Adafruit_DHT.DHT11
pin = 4 #connected to GPIO #4
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
connectedMQTT = False

while not connectedMQTT:
    try:
        client.connect(localBroker, localPort, localTimeOut)
        connectedMQTT = True
    except:
        print("Connection to MQTT broker failed")
        time.sleep(1)


while True:
    client.loop_start()
    time.sleep(SAMPLE_DELAY)
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
        client.publish(TEMPERATURE_CHIPA, payload=temperature, qos=1, retain=False)
        client.publish(HUMIDITY_CHIPA, payload=humidity, qos=1, retain=False)
    else:
        print('Failed to get reading. Try again!')

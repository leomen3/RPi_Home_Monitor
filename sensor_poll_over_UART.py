#!/usr/bin/env python
 ###########################################################################
# 1) poll sensors over UART
# 2) send samples to the MQTT broker
###########################################################################

import paho.mqtt.client as mqtt
import time
import serial
import json
import sys

RPi_HOST = "10.0.0.19"
localBroker = RPi_HOST		# Local MQTT broker
localPort = 1883			# Local MQTT port

SENSOR_PREFIX = "SENSOR:"
localTimeOut = 120


def on_connect(client, userdata, flags, rc):
    #MQTT configs
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")

def on_message(client, userdata, msg):
    print("Message received by sensor poll")
    return

def handleReading(topic,value):
    client.publish(topic, payload=value, qos=0, retain=False)
    #print('published: ',topic,":",value)
    return

def on_log(client, userdata, level, buf):
    print("UTC: ", time.ctime(), "log: ", buf)

client = mqtt.Client("environmental_poller")
client.on_connect = on_connect
#client.on_message = on_message
client.on_log = on_log
connectedMQTT = False


while not connectedMQTT:
    try:
        client.connect(localBroker, localPort, localTimeOut)
        connectedMQTT = True
    except:
        print("Connection to MQTT broker failed")
        time.sleep(1)


client.loop_start()
ser = serial.Serial('/dev/ttyUSB0', 115200)
while True:
    rawBuf = ser.readline()
    #print("Received: ",rawBuf)
    try:
        if SENSOR_PREFIX in rawBuf:
            reading = json.loads(rawBuf)
            topic = reading[2]
            value = reading[1]
            #print("Received: ",topic,value)
            handleReading(topic,value)
        else:
            #print("Unknown serial data from WeMos at UTC ",time.ctime() )
            #print("data: ",rawBuf )
            pass
    except:
        print("Oops!",sys.exc_info()[0],"occured.")

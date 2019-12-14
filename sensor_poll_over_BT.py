#!/usr/bin/env python
 ###########################################################################
# 1) poll sensors over BT (over regular serial link)
# 2) send samples to the MQTT broker
###########################################################################

import paho.mqtt.client as mqtt
import time
import json
import sys
from bluetooth import *


RPi_HOST = "10.0.0.19"
localBroker = RPi_HOST		# Local MQTT broker
localPort = 1883			# Local MQTT port
BT_MAC = "00:18:E4:40:00:06"

SOUND_ALARM_CODE = "BBBB"
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
    client.publish(topic, payload=value, qos=1, retain=True)
    print('published: ',topic,":",value)
    return

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

def init():
    global client
    global client_socket
    connectedMQTT = False
    connectedBT = False
    print("Connecting to MQTT")
    while not connectedMQTT:
        try:
            client.connect(localBroker, localPort, localTimeOut)
            connectedMQTT = True
        except:
            print("Connection to MQTT broker failed")
            time.sleep(1)

    client.loop_start()

    #establish BT socket
    print("Connecting to RFCOMM")
    while not connectedBT:
        try:
            client_socket = BluetoothSocket(RFCOMM)
            client_socket.connect((BT_MAC, 1))
            connectedBT = True
        except Exception as e:
            print(e)
            print("Connection to BT host failed")
            time.sleep(1)
def run():
    global client_socket
    while True:
        try:
            rawBuf = client_socket.recv(1024)
            print("Received: ", rawBuf)
            if SOUND_ALARM_CODE in str(rawBuf):
    #            reading = json.loads(rawBuf)
                topic = "/sensor/livingRoom/alarm"
                value = "1"
                print("Received: ", topic, value, "at UTC: ", time.ctime())
                handleReading(topic,value)
            else:
                print("Unknown serial data from BT (rfcomm) at UTC ",time.ctime() )
                print("data: ",rawBuf )
        except Exception as e:
            print(e)
            client_socket.close()
            #print("Oops!",sys.exc_info()[0],"occured.")

while True:
    try:
        init()
        run()
    except Exception as e:
        print(e)
        pass


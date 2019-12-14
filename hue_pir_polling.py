import time
import datetime as dt
import os
import sys
import json
import requests
import paho.mqtt.client as mqtt


__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))
# get configuration from json
with open(os.path.join(__location__, 'config.json'), 'r') as f:
    config = json.load(f)

hue_bridge_ip = config['HUE_BRIDGE_IP']
hue_user_name = config['HUE_USER']
motion_sensor_id = config['MOTION_SENSOR_ID']
RPi_HOST = config['RPi_HOST']
localBroker = RPi_HOST		# Local MQTT broker
localPort = 1883			# Local MQTT port
localTimeOut = 120			# Local MQTT session timeout
pir_url = 'http://' + hue_bridge_ip + '/api/' + hue_user_name + '/sensors/'+motion_sensor_id

def HUE_bridge_ip():
  "Use Philips recommended method to automatically discover HUE bridge IP"
  response = requests.get("https://discovery.meethue.com")
  hue_bridge_ip = response.json()[0]['internalipaddress']
  return hue_bridge_ip

def getPirState():
  response = requests.get(pir_url)
  json_data = json.loads(response.text)
  return json_data['state']['presence'] is True


def on_connect(client, userdata, flags, rc):
    #MQTT configs
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")


def on_message(client, userdata, msg):
    print("Message received by sensor poll")
    return


def handleReading(topic, value):
    client.publish(topic, payload=value, qos=1, retain=True)
    print('published: ', topic, ":", value)
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

    client.loop_start


def run():
  while True:
    try:
      now = dt.datetime.now()
      isPresenceDetected = getPirState()
      if isPresenceDetected == True:
        topic = "/sensor/MotionHUE"
        value = "1"
        handleReading(topic, value)
      print("Motion sensor status is: ", isPresenceDetected)

      # if pir is True:
      #   lastAction = now
      #   if state != 1:
      #     state = 1
      # elif pir is False and (now - lastAction).total_seconds() > COOL_DOWN:
      #   lastAction = now
      #   state = 0

      time.sleep(5) 
    except Exception as e:
      print(e)


while True:
    try:
        init()
        run()
    except Exception as e:
        print(e)
        pass

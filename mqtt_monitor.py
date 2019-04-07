#!/usr/bin/env python
 ###########################################################################
# 1) connect to the MQTT broker
# 2) subscribe to the available data streams
# 3) log to google sheets
# 4) notify on critical events on the telegram channel
###########################################################################

import time
import os
import string
import paho.mqtt.client as mqtt
import requests
from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import telepot
import json

RPi_HOST = "10.0.0.19"
localBroker = RPi_HOST		# Local MQTT broker
localPort = 1883			# Local MQTT port
UTC_OFFSET = 3   # hours of differenc between UTC and local (Jerusalem) time
RECORD_INTERVAL = 5*60   #number if seconds between subsequent recods in google sheets
HOME_DIR = '/home/pi'   #home directory
localTimeOut = 120			# Local MQTT session timeout
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
last_record = {}

# get configuration from json
with open( os.path.join(__location__, 'config.json'), 'r') as f:
    config = json.load(f)

telegramToken = config['telegramToken']
SPREADSHEET_ID = config['SPREADSHEET_ID']
API_KEY = config['API_KEY']
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'
NUM_ENTRIES_CELL = "InputData!E2"
SHEET_ID = 0

#limits
MAX_TEMPERATURE = 30
MIN_TEMPERATURE = 15
topicsOfInterest = ["/sensor/Chipa/humidity",
    "/sensor/Chipa/temperature",
    "/sensor/Chipa/CO",
    "/sensor/Chipa/All_Gas"]
CARBON_MONOXIDE_ADC_THRESH = 3000
GAS_ALL_ADC_THRESH = 4500


def getDateTime():
    return time.ctime()


def pushSample(sample, topic):
    global client
    client.publish(topic, str(sample))


#Generic Init
print ("Initializing...")


def on_connect(client, userdata, flags, rc):
    #MQTT configs
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")


def notifyTelegram(message):
    print("Notifying Telegram: "+message)
    bot.sendMessage(504721552, message)


def limitsExsess(topic, value):
    """ Check the value for limits according to topic.
    If out of limit, notify over telegram"""

    val = float(value)
    if "temperature" in topic:
        if val < MIN_TEMPERATURE or val > MAX_TEMPERATURE:
            notifyTelegram("Temperature out of bounds: "+value+"degC")
            return True
    if "CO" in topic:
        if  val > CARBON_MONOXIDE_ADC_THRESH:
            notifyTelegram("Carbon Monoxide level above threshold: "+value)
            return True
    if "All_Gas" in topic:
        if  val > GAS_ALL_ADC_THRESH:
            notifyTelegram("Poison gas level above threshold: "+value)
            return True
    return False


def on_message(client, userdata, msg):
    # The callback for when a PUBLISH message is received from the server.
    global service
    global last_record
    currTime = getDateTime()
    topic = msg.topic
    print("time: "+str(currTime)+","+msg.topic+" "+str(msg.payload))
    if topic not in topicsOfInterest:
        print("Topic: ",topic," from ",msg," not in the interest list")
        return
    if topic not in last_record:
        last_record[topic] = 0
    value = str(msg.payload)
    timer = time.time()
    if limitsExsess(topic, value) or ((timer-last_record[topic]) > RECORD_INTERVAL):
        print("Updating records")
        update_records(topic, value)
        last_record[topic] = timer    
    return


def on_disconnect(client, userdata,rc=0):
    print("DisConnected result code "+str(rc))
    client.loop_stop()


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    #home_dir = os.path.expanduser('~')
    home_dir = (HOME_DIR)
    credential_dir = os.path.join(home_dir, '.credentials')
    print("Credentials folder: ",credential_dir)
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def create_service():
    credentials = get_credentials()
    service = discovery.build('sheets', 'v4', credentials=credentials)
    return service


def number_of_entries(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=NUM_ENTRIES_CELL).execute()
    value = result.get('values', [])
    return int(value[0][0])


def update_records(topic, value):
    global seconds
    entries = number_of_entries(service)
    currTime = getDateTime()
    line_num = str(2 + entries)
    range = "InputData!A"+line_num+":D"+line_num

    # How the input data should be interpreted.
    value_input_option = 'USER_ENTERED'

    values = [ [ currTime, topic, value  ] ]
    body = {'values': values}

    request = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, 
            range=range, 
            valueInputOption=value_input_option, 
            body=body)

    response = request.execute()
    update_entries(service,entries+1)
    return response


def update_entries(service,entries):
    range = NUM_ENTRIES_CELL
    value_input_option = 'USER_ENTERED'
    values = [
        [
           entries
        ] ]
    body = {'values': values}
    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=range,
                                                     valueInputOption=value_input_option, body=body
                                                     )
    response = request.execute()
    return response

if __name__ == "__main__":
    global service
    connectedGoogle = False
    connectedMQTT = False

    #establish Telegram Bot
    bot = telepot.Bot(telegramToken)
    bot.getMe()

    while not connectedGoogle:
        try:
            service = create_service()
            connectedGoogle = True
        except:
            print ("failed to connect to google sheets, retrying")
            time.sleep(1)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while not connectedMQTT:
        try:
            client.connect(localBroker, localPort, keepalive = 6000)
            connectedMQTT = True
        except:
            print("Connection to MQTT broker failed")
            time.sleep(1)
    
    client.loop_start()
    while True:
        time.sleep(10)
        client.publish("/empty",None)
#!/bin/python
from influxdb import InfluxDBClient
import time
import datetime

db = 'try1'

dbclient = InfluxDBClient("10.0.0.19", 8086, 'leo', '333')

#print("Create DB:")
#dbclient.create_database('try1')

print("Databases:")
dbclient.get_list_database()

for i in range (100):
    receiveTime = datetime.datetime.utcnow()
    json_body = [
        {
            "measurement": "test",
            "time": receiveTime,
            "fields": {
                "value": 101.1
            }
        }
    ]
    time.sleep(1)
    print("Writing iteration number: ",str(i), " to db")
    dbclient.write_points(points = json_body,database = db)


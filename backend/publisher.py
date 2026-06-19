import paho.mqtt.client as mqtt 
import paho.mqtt.publish as publish
from backend.cns.server import get_packet
from datetime import datetime
import random 
import ssl
from dotenv import load_dotenv
import os
from dataclasses import asdict
import json 

load_dotenv()

CLUSTER_USERNAME = os.getenv("CLUSTER_USERNAME")
CLUSTER_PASSWORD = os.getenv("CLUSTER_PASSWORD")
CLUSTER_URL = os.getenv("CLUSTER_URL")

def on_connect(client, userdata, flags, rc):
    print("CONNAK recieved with code: " + str(rc)) 

#Initializing both files to empty
with open ("parsed_data_log.txt", "w") as file:
    file.write("")

with open ("RecvMonitorData.txt", "w") as file:
    file.write("")

with open ("subscriber_log.txt", "w") as file:
    file.write("")

client = mqtt.Client()
client.username_pw_set(CLUSTER_USERNAME, CLUSTER_PASSWORD)
client.on_connect = on_connect 

client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.connect(CLUSTER_URL, 8883)  


client.loop_start() 

for message in get_packet(): 
    #print("MESSAGE: ", message, type(message))
    payload = asdict(message)
    payload["timestamp"] = str(datetime.now())

    (rc, mid) = client.publish("temptest/temperature", json.dumps(payload), qos = 0)

        #client.publish("temptest/temperature", "END OF STREAMING", qos =1)

client.loop_stop()
client.disconnect()






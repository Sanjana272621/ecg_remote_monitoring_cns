import paho.mqtt.client as mqtt 
import paho.mqtt.publish as publish
import ssl 
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import telemetry_service as telemetry_service 
from fastapi import Request
import asyncio
import os
import json

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

CLUSTER_USERNAME = os.getenv("CLUSTER_USERNAME")
CLUSTER_PASSWORD = os.getenv("CLUSTER_PASSWORD")
CLUSTER_URL = os.getenv("CLUSTER_URL")

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    raw = msg.payload.decode("utf-8")
    data = json.loads(raw)
    with open("subscriber_log.txt", "a") as file:
        file.write("\nRecieved Message: \n")
        file.write(str(data))
        file.write(str(type(data)))

    telemetry_service.realtime_storage(data)
    telemetry_service.persistent_storage(data)
    #telemetry_service.realtime_storage(parsed)
    #telemetry_service.persistent_storage(parsed)
    #telemetry_service.view_buffers()

    #print(hl7_parser.parse_hl7_message(msg.payload))

def on_connect(client, userdata, flags, rc):
    print("CONNAK recieved with code: " + str(rc)) 

client = mqtt.Client()
client.username_pw_set(CLUSTER_USERNAME, CLUSTER_PASSWORD)
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_connect = on_connect 

client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.connect(CLUSTER_URL, 8883)  

client.subscribe("temptest/temperature", qos=1)
client.loop_start()

#FastAPI Routes
@app.get("/ecg_vitals")
def get_ecg_vitals_route():
    return telemetry_service.get_ecg_vitals()

@app.get("/resp_vitals")
def get_resp_vitals_route():
    return telemetry_service.get_resp_vitals()

@app.get("/spo2_vitals")
def get_spo2_vitals_route():
    return telemetry_service.get_spo2_vitals()

@app.get("/temp_vitals")
def get_temp_vitals_route():
    return telemetry_service.get_temp_vitals()

@app.get("/nibp_vitals")
def get_nibp_vitals_route():
    return telemetry_service.get_nibp_vitals()


@app.websocket("/waveform")
async def waveform_socket(ws: WebSocket):
    await ws.accept()

    while True:
        data = telemetry_service.get_latest_ecgI_waveform()
        await ws.send_json(data)
        await asyncio.sleep(0.001)
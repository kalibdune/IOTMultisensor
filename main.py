from typing import Union
import st_con
from fastapi import FastAPI, Request, Body
from fastapi.responses import RedirectResponse
import time
import requests
import json
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException


def on_connect(client, userdata, flags, rc):
    client.subscribe("Dmitry/rele")
    client.subscribe("Dmitry/data")
    print("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    if msg.topic == 'Dmitry/data':
        data = json.loads(msg.payload)
        set_temp_hum(data)



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("levandrovskiy.ru", 1883, 60)
client.loop_start()


app = FastAPI()

def set_temp_hum(data):
    st.send_temp_hum(data["temp"], data["hum"])

def btn(state):
    data = {"rele": False if state == "off" else True}
    print(data)
    data = json.dumps(data)
    client.publish("Dmitry/rele", data) 


clientId = "bcf8e9db-46c8-4215-b480-9dcee92f006e"
clientSecret = "eca95cd7c4fb7b03af4bee278d9372a0f11c95d5448daa2b9b9cc1955726f86bb153a635afa71bec5de298ac67ae3a105ce53d5c5a2c9d8292d6ea05be6a0dd0820d31b20cdf6936c4ec66b0dca536cf625ee65feb1fb0c39f08b1a41ce80c8cd7c52620ebb9092b54359b135b0ceb5533a0f1fdd5b9e719774bfbb52d1ab6cadee7ca1a4a0280db14ec03a6555bc3f90471555a6fc1f033789ee4a91545391edcfe6c583de615ae78203dbc036689674d2046e5967398901e03b9d2a391ec7fdcebc8dc9ad0d788d3981b7f4110f8ea222f88f3e3265ae70636ee967089b2af29bc90e681f3c9bee5e7e035cd73f6388b1a0c5c0eefe410ff8387fd4873d5e9"
deviceProfileID = "7cc1999d-083c-49d8-9e84-78fed8fa20fc"

st = st_con.SmartThingsCon(btn, clientId, clientSecret, deviceProfileID)
app = FastAPI()

@app.get("/kalibdune/test_btn")
async def ffff(state):
      st.send_btn(state)

@app.get("/")
async def hello():
    return {"hello": "hello"}

@app.post("/kalibdune")
async def show_body(data = Body()):
    body_content = data
    type, tt = st.read_response(data)
    return tt

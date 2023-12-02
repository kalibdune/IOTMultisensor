import json
import requests

class SmartThingsCon:
    BASE_URL = "https://c2c-eu.smartthings.com/device/events"

    def __init__(self, btn_handler, clientId, clientSecret, deviceProfileID):
        self.Token = None
        self.dev_1_state = self._create_default_state("stateCallback")
        self.dev_1_state["deviceState"] = [self._build_state("partner-device-id-1", "st.switch", "switch", 'on')]
        self.dev_2_state = self._create_default_state("stateCallback")
        self.dev_2_state["deviceState"] = [self._build_state("partner-device-id-2", "st.temperatureMeasurement", "temperature", 20, "C", stat=
                            self._build_state("partner-device-id-2", "st.relativeHumidityMeasurement", "humidity", 20))]
        self.schema = ""
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.deviceProfileID = deviceProfileID
        self.btn_handler = btn_handler

    def _create_default_state(self, interaction_type):
        return {
            "headers": {
                "schema": "st-schema",
                "version": "1.0",
                "interactionType": interaction_type,
                "requestId": "abc-123-456"
            },
            "authentication": {"tokenType": "Bearer", "token": ""},
            "deviceState": []
        }

    def _get_token(self, code, url):
        response = requests.post(url, data=json.dumps({
            "headers": {
                "schema": "st-schema",
                "version": "1.0",
                "interactionType": "accessTokenRequest",
                "requestId": "abc-123-456"
            },
            "callbackAuthentication": {
                "grantType": "authorization_code",
                "code": code,
                "clientId": self.clientId,
                "clientSecret": self.clientSecret
            }
        }))
        print('accessToken',response.json())
        return response.json()['callbackAuthentication']['accessToken']

    def _build_state(self, external_device_id, capability, attribute, value, unit=None, stat=None, component = "main"):
        state = {
            "externalDeviceId": external_device_id,
            "deviceCookie": {},
            "states": [{"component": component, "capability": capability, "attribute": attribute, "value": value}]
        }
        if unit:
            state["states"][0]["unit"] = unit
        if stat:
            state["states"].append(stat["states"][0])
        return state

    def _build_callback_headers(self, interaction_type, request_id):
        return {
            "headers": {
                "schema": "st-schema",
                "version": "1.0",
                "interactionType": interaction_type,
                "requestId": request_id
            }
        }

    def _send_event(self, state):
        state['authentication']['token'] = self.Token
        r = requests.post(self.BASE_URL, data=json.dumps(state))
        print(r.json())

    def read_response(self, resp):
        print(resp)

        interaction_type = resp['headers']['interactionType']

        if interaction_type == 'grantCallbackAccess':
            code = resp['callbackAuthentication']['code']
            url = resp['callbackUrls']['oauthToken']
            self.Token = self._get_token(code, url)
            return 'grantCallbackAccess', self._getSchema()

        if interaction_type == 'discoveryRequest':
            return 'discoveryRequest', self._getSchema()

        if interaction_type == 'interactionResult':
            if 'globalError' in resp.keys():
                print("ОШИБКА", resp['globalError'])
                return "", ""
            return 'interactionResult', resp['deviceState']

        if interaction_type == 'stateRefreshRequest':
            request_id = resp['headers']['requestId']
            self.stateRefreshRequest = self._create_default_state('stateRefreshResponse')
            self.stateRefreshRequest['headers']['requestId'] = request_id
            if len(resp['devices']) == 2:
                print(self.dev_1_state)
                print(self.dev_2_state)
                self.stateRefreshRequest['deviceState'] = [self.dev_1_state['deviceState'][0], self.dev_2_state['deviceState'][0]]
            elif resp['devices'][0]['externalDeviceId'] == "partner-device-id-1":
                self.stateRefreshRequest['deviceState'] = [self.dev_1_state['deviceState'][0]]
            elif resp['devices'][0]['externalDeviceId'] == "partner-device-id-2":
                self.stateRefreshRequest['deviceState'] = [self.dev_2_state['deviceState'][0]]
            return 'stateRefreshRequest', self.stateRefreshRequest

        if interaction_type == 'commandRequest':
            request_id = resp['headers']['requestId']
            self.dev_1_state['headers']['requestId'] = request_id
            self.dev_1_state['headers']['interactionType'] = "commandResponse"
            self.dev_1_state['deviceState'][0]['states'][0]['value'] = resp['devices'][0]['commands'][0]['command']
            self.btn_handler(resp['devices'][0]['commands'][0]['command'])
            return 'commandRequest', self.dev_1_state

        if interaction_type == 'integrationDeleted':
            return 'integrationDeleted', self._getSchema()
        
    def send_btn(self, state):
        self.dev_1_state['headers']['interactionType'] = "stateCallback"
        self.dev_1_state["deviceState"] = [self._build_state("partner-device-id-1", "st.switch", "switch", state)]
        self._send_event(self.dev_1_state)

    def send_temp_hum(self, temp: int, hum: int):
        self.dev_2_state['headers']['interactionType'] = "stateCallback"
        self.dev_2_state["deviceState"] = [self._build_state("partner-device-id-2", "st.temperatureMeasurement", "temperature", temp, "C", stat=
                           self._build_state("partner-device-id-2", "st.relativeHumidityMeasurement", "humidity", hum))]
        self._send_event(self.dev_2_state)

    def _getSchema(self, requestId = "abc-123-456"):
        return {
                "headers": {
                    "schema": "st-schema",
                    "version": "1.0",
                    "interactionType": "discoveryResponse",
                    "requestId": requestId
                },
                "requestGrantCallbackAccess": True,
                "devices": [
                        {
                        "externalDeviceId": "partner-device-id-1",
                        "deviceCookie": {"updatedcookie": "old or new value"},
                        "friendlyName": "Kitchen Bulb",
                        "manufacturerInfo": {
                            "manufacturerName": "LIFX",
                            "modelName": "A19 Color Bulb",
                            "hwVersion": "v1 US bulb",
                            "swVersion": "23.123.231"
                        },
                        "deviceContext" : {
                            "roomName": "Kitchen",
                            "groups": ["Kitchen Lights", "House Bulbs"],
                            "categories": ["light", "switch"]
                        },
                        "deviceHandlerType": "c2c-rgbw-color-bulb",
                        "deviceUniqueId": "unique identifier of device"
                        },
                        {
                        "externalDeviceId": "partner-device-id-2",
                        "deviceCookie": {"updatedcookie": "old or new value"},
                        "friendlyName": "Multi sensor",
                        "manufacturerInfo": {
                            "manufacturerName": "LIFX",
                            "modelName": "Outlet",
                            "hwVersion": "v1 US outlet",
                            "swVersion": "3.03.11"
                        },
                        "deviceContext" : {
                            "roomName": "Kitchen",
                            "groups": ["Hall Lights"],
                            "categories": ["MultiFunctionalSensor"]
                        },
                        "deviceHandlerType": self.deviceProfileID,
                        "deviceUniqueId": "unique identifier of device"
                        }
                    ]
                }
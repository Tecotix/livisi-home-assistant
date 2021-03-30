from ratelimit import limits, RateLimitException

import json
import logging
import pickle
import time
import ssl
from collections import namedtuple
from pprint import pformat, pprint
from threading import Thread
import asyncio
import websockets

import colorlog
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError, MissingTokenError
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from .innogy_event import *
from .innopy_constants import *
from .innogy_device import *
from .util import *

_LOGGER = logging.getLogger(__name__)
#handler = colorlog.StreamHandler()
#f_handler = logging.FileHandler("innopy.log")
s_handler = logging.StreamHandler()
#handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(levelname)s:\t%(asctime)s:\t%(message)s'))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#f_handler.setFormatter(formatter)
s_handler.setFormatter(formatter)
_LOGGER.setLevel(logging.INFO)
_LOGGER.addHandler(s_handler)
#_LOGGER.addHandler(f_handler)


#https://api.services-smarthome.de/AUTH/authorize?response_type=code&client_id=24635748&redirect_uri=https%3A%2F%2Fwww.ollie.in%2Finnogy-smarthome-token%2F&scope&lang=de-DE
client_id = CLIENT_ID_INNOGY_SMARTHOME
client_secret = CLIENT_SECRET_INNOGY_SMARTHOME
redirect_uri = REDIRECT_URL_INNOGY_SMARTHOME
scope=[]

class InnopyClient(object):

    @property
    def thermostats(self) :
        rsts =  [x for x in self.devices if x.type=="RST"]
        return [ x for x in rsts if x.device_state_dict["IsReachable"]["value"]==True]

    def __init__(self,token):
        self.token = token
        _LOGGER.debug(pformat(self.token["access_token"]))
        self.oauth = OAuth2Session(client_id=client_id, token=self.token, auto_refresh_url=API_URL_TOKEN)


        self.initialize()
        self.devices = list()
        self._capability_device_dict = {}
        full_devs = self.get_full_devices() 
        for dev_id in full_devs:
            device = InnogyDevice(self,full_devs[dev_id])
            #id - device
            for capability in device.capabilities_dict:
                _LOGGER.info("capability "+ str(capability))
                self._capability_device_dict.update({device.capabilities_dict[capability]["id"]:device})

            self.devices.append(device)
        _LOGGER.info("innopy initalized...")

    def get_device_by_capability_id(self, capability_id):
        device = self._capability_device_dict[capability_id]
        _LOGGER.info(capability_id + " resolved to " + device.config_dict["Name"])
        return device

    

    @limits(calls=100, period=60)
    def call_innogy_api(self,url, json_data=None):
        for i in range(API_CALL_RETRY_ATTEMPTS): 
            try:
                if json_data:
                    resp = self.oauth.post(url, json=json_data)
                else:
                    resp = self.oauth.get(url)
                _LOGGER.debug(pformat(resp.json()))
                self._handle_response_errors(resp)
                return resp.json()
            
            except (TokenExpiredError, MissingTokenError):
                self.token = self.oauth.refresh_token(token_url=API_URL_TOKEN, refresh_token=self.token["refresh_token"], auth=HTTPBasicAuth(client_id, client_secret))
                _LOGGER.warn("token refreshed, retrying in 2 seconds...")
                time.sleep(2)


        

    def _handle_response_errors(self, response):
        if response.status_code == 200:
            _LOGGER.debug("status code is OK")
            return
        elif response.status_code == 503:
            _LOGGER.error("innogy service is unavailabe (503).")
        else:
            _LOGGER.error("status code is NOT OK: "+ str(response.status_code));
            try:
                resp_json = response.json()
                errorcode = resp_json["errorcode"]
            except:
                if not errorcode:
                    content = response.text
                    _LOGGER.error("response error content: " + str(pformat(content)) )
                    return

            if errorcode == ERR_SESSION_EXISTS:
                _LOGGER.warn(str(resp_json["description"]))
            elif errorcode == ERR_SESSION_NOT_FOUND:
                _LOGGER.warn(str(resp_json["description"]))
            elif errorcode == ERR_CONTROLLER_OFFLINE:
                _LOGGER.warn(str(resp_json["description"]))
            elif errorcode == ERR_REMOTE_ACCESS_NOT_ALLOWED:
                _LOGGER.warn("Remote access not allowed. Access is allowed only from the SHC device network.")
            elif errorcode == ERR_REMOTE_ACCESS_NOT_ALLOWED:
                _LOGGER.warn(str(resp_json["description"]))
            elif errorcode == ERR_INVALID_ACTION_TRIGGERED:
                _LOGGER.warn(str(resp_json["description"]))
            else:
                _LOGGER.error(str(resp_json["description"]))


    def initialize(self):
        _LOGGER.info(API_URL_INITIALIZE)
        resp = self.call_innogy_api(API_URL_INITIALIZE)
        return resp

    def uninitialize(self):
        _LOGGER.info(API_URL_UNINITIALIZE)
        resp = self.call_innogy_api(API_URL_UNINITIALIZE)
        return resp

    def get_devices(self):
        _LOGGER.info(API_URL_DEVICE)
        resp = self.call_innogy_api(API_URL_DEVICE)
        return resp

    def get_device_by_id(self, device_id):
        _LOGGER.info(API_URL_DEVICE_ID.replace("{id}", device_id))
        resp = self.call_innogy_api(API_URL_DEVICE_ID.replace("{id}", device_id))
        return resp

    def get_device_states(self):
        _LOGGER.info(API_URL_DEVICE_STATES)
        resp = self.call_innogy_api(API_URL_DEVICE_STATES)
        return resp

    def get_locations(self):
        _LOGGER.info(API_URL_LOCATION)
        resp = self.call_innogy_api(API_URL_LOCATION)
        return resp

    def get_messages(self):
        _LOGGER.info(API_URL_MESSAGE)
        resp = self.call_innogy_api(API_URL_MESSAGE)
        return resp

    def get_capabilities(self):
        _LOGGER.info(API_URL_CAPABILITY)
        resp = self.call_innogy_api(API_URL_CAPABILITY)
        return resp

    def get_capability_states(self):
        _LOGGER.info(API_URL_CAPABILITY_STATES)
        resp = self.call_innogy_api(API_URL_CAPABILITY_STATES)
        return resp

    def get_device_capabilites_by_id(self, device_id):
        _LOGGER.info(API_URL_DEVICE_CAPABILITIES.replace("{id}",device_id))
        resp = self.call_innogy_api(API_URL_DEVICE_CAPABILITIES.replace("{id}",device_id))
        return resp

    def get_device_state_by_id(self,device_id):
        _LOGGER.info(API_URL_DEVICE_ID_STATE.replace("{id}",device_id))
        resp = self.call_innogy_api(API_URL_DEVICE_ID_STATE.replace("{id}",device_id))
        return resp

  
    def get_full_devices(self):
        locations = self.get_locations()
        location_dict = list_to_id_dict(locations)
        _LOGGER.debug(pformat(location_dict))

        caps = self.get_capabilities()
        caps_dict = list_to_id_dict(caps)
        _LOGGER.debug(pformat(caps_dict))

        cap_states = self.get_capability_states()
        cap_states_dict = list_to_id_dict(cap_states)
        _LOGGER.debug(pformat(cap_states_dict))

        dev_states = self.get_device_states()
        dev_states_dict = list_to_id_dict(dev_states)
        _LOGGER.debug(pformat(dev_states_dict))

        messages = self.get_messages()
        # TODO: handle device messages
        # https://github.com/ollie-dev/openhab2-addons/blob/master/addons/binding/org.openhab.binding.innogysmarthome/src/main/java/org/openhab/binding/innogysmarthome/internal/client/InnogyClient.java

        #_dict = list_to_id_dict(caps)
        #_LOGGER.debug(pformat(_dict))

        devs = self.get_devices()
        devs_dict = list_to_id_dict(devs)

        for dev_id in devs_dict:
            dev = devs_dict[dev_id]
            _LOGGER.info(dev_id)

            # TODO: check for battery powered
            #  if (BATTERY_POWERED_DEVICES.contains(d.getType())) {
            #     d.setIsBatteryPowered(true);
            
            _LOGGER.info("resolving location ...")
            if "Location" in dev:
                for loc_link in dev["Location"]:
                    dev_loc_id = loc_link["value"].replace("/location/","")
                    loc_link["resolved"] = location_dict[dev_loc_id]["Config"]
            else:
                _LOGGER.warn("no device locations")

            _LOGGER.info("resolving capabilities and capability states ...")
            if "Capabilities" in dev:
                #dev_cap_states = {}
                dev_cap_links = dev["Capabilities"]
                for cap_link in dev_cap_links:
                    cap = caps_dict[cap_link["value"].replace("/capability/","")]
                    cap_id = cap["id"]
                    if cap_id in cap_states_dict:
                        
                        cap_state = cap_states_dict[cap_id]
                        cap_link["resolved"] = cap_state["State"]
                        #dev_cap_states[cap_id] = cap_state
                    else:
                        _LOGGER.warn("capability not resolved")

                #dev["resolved_capabilities"] = dev_cap_states

            _LOGGER.info("resolving device states ...")
            if dev_id in dev_states_dict:
                dev_state = dev_states_dict[dev_id]
                dev["device_state"] = dev_state["State"]
            else:
                _LOGGER.warn("device_state_unknown")
            
            _LOGGER.debug(pformat(dev))
        return devs_dict
            
    def get_full_device_by_id(self, device_id):
        locations = self.get_locations()
        location_dict = list_to_id_dict(locations)
        _LOGGER.debug(pformat(location_dict))

        caps = self.get_device_capabilites_by_id(device_id)
        caps_dict = list_to_id_dict(caps)
        _LOGGER.debug(pformat(caps_dict))

        cap_states = self.get_capability_states()
        cap_states_dict = list_to_id_dict(cap_states)
        _LOGGER.debug(pformat(cap_states_dict))

        dev_state = self.get_device_state_by_id(device_id)
        _LOGGER.debug(pformat(dev_state))

        messages = self.get_messages()
        # TODO: handle device messages
        # https://github.com/ollie-dev/openhab2-addons/blob/master/addons/binding/org.openhab.binding.innogysmarthome/src/main/java/org/openhab/binding/innogysmarthome/internal/client/InnogyClient.java

        #_dict = list_to_id_dict(caps)
        #_LOGGER.debug(pformat(_dict))

        dev = self.get_device_by_id(device_id)
        dev_dict = dev

        # TODO: check for battery powered
        #  if (BATTERY_POWERED_DEVICES.contains(d.getType())) {
        #     d.setIsBatteryPowered(true);
        
        _LOGGER.info("resolving location ...")
        if "Location" in dev:
            for loc_link in dev["Location"]:
                dev_loc_id = loc_link["value"].replace("/location/","")
                loc_link["resolved"] = location_dict[dev_loc_id]["Config"]
        else:
            _LOGGER.warn("no device locations")
    

        _LOGGER.info("resolving capabilities and capability states ...")
        if "Capabilities" in dev:
            dev_cap_states = {}
            dev_cap_links = dev["Capabilities"]
            for cap_link in dev_cap_links:
                cap = caps_dict[cap_link["value"].replace("/capability/","")]
                cap_id = cap["id"]
                if cap_id in cap_states_dict:
                    cap_state = cap_states_dict[cap_id]
                    dev_cap_states[cap_id] = cap_state
                    cap_link["resolved"] = cap_state["State"]
                else:
                    _LOGGER.warn("capability not resolved")

        _LOGGER.info("resolving device states ...")
        if not "errorcode" in dev_state:
            dev_dict["device_state"] = dev_state
        else:
            _LOGGER.warn(dev_state["messages"][0])
        
        _LOGGER.debug(pformat(dev))
        return dev_dict
    
    def subscribe_events(self):
        _LOGGER.info("starting innogy event handler")
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self._innogy_event_handler())

    @asyncio.coroutine
    def _innogy_event_handler(self):
#        websocket = yield from websockets.connect(API_URL_EVENTS.replace("{token}",self.token["access_token"]),sslopt={"cert_reqs": ssl.CERT_NONE})
        while True:
            try:
                _LOGGER.warning("connecting websocket")
                websocket = yield from websockets.connect(API_URL_EVENTS.replace("{token}",self.token["access_token"]))
                _LOGGER.warning("websocket connected")
        
                _LOGGER.warning("waiting for event ...")
                response = yield from websocket.recv()
                result = json.loads(response)
                        
                for evt in result:
                    try:
                        self._handle_event(evt,websocket)
                        _LOGGER.info("... event handled")
                    except Exception as e:
                        import traceback
                        _LOGGER.error(traceback.format_exc(e))
            except Exception as e:
                _LOGGER.warning(str(e))
            finally:
                yield from websocket.close()
                self.initialize()
        
        # while True:
            
        #         self.initialize()
        #         _LOGGER.warn("connecting websocket")
        #         ws = create_connection(API_URL_EVENTS.replace("{token}",self.token["access_token"]),sslopt={"cert_reqs": ssl.CERT_NONE})
        #         _LOGGER.warn("... websocket connected")

        #         while ws.connected:
        #             _LOGGER.info("waiting for event ...")
        #             result_json =  ws.recv()
        #             result = json.loads(result_json)
                    
        #             for evt in result:
        #                 try:
        #                     self._handle_event(evt,ws)
        #                     _LOGGER.info("... event handled")
        #                 except Exception as e:
        #                     import traceback
        #                     _LOGGER.error(traceback.format_exc(e))
                    
        #         _LOGGER.warn("Socket disconnected reconnecting ...")
        #         time.sleep(3)
                

    def _handle_event(self,evt, websocket):
        try:
            _LOGGER.warning("new event ...")
            _LOGGER.warning(pformat(evt))
            event = InnogyEvent(evt)

            if event.type == '/event/Disconnect':
                _LOGGER.info("DISCONNECT EVENT!")
                _LOGGER.debug(pformat(evt))
                _LOGGER.info("closing websocket ...")
                websocket.close()
                return

            _LOGGER.info("getting change value")
            cap_id = event.link_dict["value"]
            device = self.get_device_by_capability_id(cap_id)
            _LOGGER.info(device.config_dict["Name"])
            for prop_name in event.properties_dict.keys():
                device.capabilities_dict[prop_name]["value"] = event.properties_dict[prop_name]["value"]

            if "lastchanged" in event.properties_dict[prop_name]:
                device.capabilities_dict[prop_name]["lastchanged"] = event.properties_dict[prop_name]["lastchanged"]
                _LOGGER.info("updated " + str(prop_name) + " to " + str(device.capabilities_dict[prop_name]["value"]))


                #{'Properties': [{'name': 'Reason', 'value': 'SessionExpired'}], 
                #'desc': '/desc/event/Disconnect', 
                #'timestamp': '2018-05-01T22:10:35.2825559Z', 
                #'type': '/event/Disconnect'} :
            _LOGGER.info("... event handled completely")
        except:
            _LOGGER.error("could not process event: " + pformat(evt))

    
    def set_OperationMode_state(self,capabilityId, auto_mode):
        json_data = {
        "desc":"/desc/device/SHC.RWE/1.0/action/SetState",
        #"timestamp": now.toISOString()
        "type":ACTION_TYPE_SETSTATE,
        "Link":{"value":capabilityId},
        "Data":
            [{
            "name":ACTION_PARAMETER_THERMOSTATACTUATOR_OPERATIONMODE,
            "type":"/entity/Constant",
            "Constant":{"value": "Auto" if auto_mode else "Manu"}
            }]
        }
        self.call_innogy_api(API_URL_ACTION, json_data=json_data)
        
    def set_PointTemperature_state(self,capabilityId, pointTemperature):
        json_data = {
        "desc":"/desc/device/SHC.RWE/1.0/action/SetState",
        #"timestamp": now.toISOString()
        "type":ACTION_TYPE_SETSTATE,
        "Link":{"value":capabilityId},
        "Data":
            [{
            "name":ACTION_PARAMETER_THERMOSTATACTUATOR_POINTTEMPERATURE,
            "type":"/entity/Constant",
            "Constant":{"value":pointTemperature}
            }]
        }

        self.call_innogy_api(API_URL_ACTION, json_data=json_data)

    def get_auth_token(self):
        auth = HTTPBasicAuth(client_id, client_secret)

        oauth = OAuth2Session(client_id=client_id, redirect_uri=redirect_uri)

        authorization_url, state = oauth.authorization_url(API_URL_AUTHORIZE)

        print ('Please go to %s and authorize access.', authorization_url)
        authorization_response = input('Enter the full callback URL')

        print()
        print(authorization_response)

        #get from https://api.services-smarthome.de/AUTH/authorize?response_type=code&client_id=24635748&redirect_uri=https%3A%2F%2Fwww.ollie.in%2Finnogy-smarthome-token%2F&scope&lang=de-DE
        #only valid for one use
        #auth_code="https://www.ollie.in/innogy-smarthome-token/?code=68f8e909a8bf4e2a8a6efe90060ac151"
        #token = oauth.fetch_token(API_URL_TOKEN, client_secret=client_secret, authorization_response=auth_code)
     
        #token = oauth.fetch_token(API_URL_TOKEN, auth=auth, authorization_response=authorization_response)
        token = oauth.fetch_token(API_URL_TOKEN, auth=auth, code=authorization_response)

        print()
        pickle.dump(token,open("token.p", "wb"))
        logger.info(pformat(token))
        return token

   
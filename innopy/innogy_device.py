#import .innopy_device_types
from pprint import pprint, pformat
import logging
import colorlog
_LOGGER = logging.getLogger(__name__)


def create_devices(innogy_client, device):
    devices = []
    
    i = InnogyDevice(innogy_client, device)

    return  i

class InnogyDevice():

    def __init__(self, innogy_client, device):
        self.client = innogy_client
        self._set_data(device)
        _LOGGER.info("creating device: ", device["id"])

    def _set_data(self,device):
        self.config_dict = {item["name"]:item["value"] for item in device["Config"]}
        
        self.desc = device["desc"]
        self.id = device["id"]
        
        self.manufacturer = device["manufacturer"]
        self.product = device["product"]
        self.serialnumber = device["serialnumber"]
        self.type = device["type"]
        self.version = device["version"]

        #TODO: Handle tags?

        if "device_state" in device:
            state_dict = {}
            for state in device["device_state"]:
                if "lastchanged" in state:
                    state_dict.update({state["name"]:{"value":state["value"], "lastchanged":state["lastchanged"]}})
                else:
                    state_dict.update({state["name"]:{"value":state["value"]}})

            self.device_state_dict = state_dict

        if "Capabilities" in device:
            capabilities_dict = {}
            for cap in device["Capabilities"]:
                cap_id = cap["value"]
                if "resolved" in cap:
                    for resolved in cap["resolved"]:
                        cap_name = resolved["name"]
                        cap_value = resolved["value"]
                        cap_lastchanged = resolved["lastchanged"]
                        capabilities_dict.update({cap_name:{"id": cap_id, "value":cap_value, "lastchanged":cap_lastchanged}})
            self.capabilities_dict = capabilities_dict

        if "Location" in device:
            locations_dict = {}
            for loc in device["Location"]:
                loc_id = loc["value"]
                resolved = loc["resolved"]
                loc_name = resolved[0]["value"]
                loc_type = resolved[1]["value"]
                locations_dict.update({loc_name:{"id": loc_id, "type":loc_type}})
            self.location_dict = locations_dict

    def update(self):
        _LOGGER.info("updating device...")
        device_data = self.client.get_full_device_by_id(self.id)
        self._set_data(device_data)
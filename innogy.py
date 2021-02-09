"""
Support for the (unofficial) Tado api.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tado/
"""
import logging
import urllib
from datetime import timedelta

import voluptuous as vol
from homeassistant.components.climate import (
                                        ATTR_CURRENT_HUMIDITY,
                                              ATTR_CURRENT_TEMPERATURE,
                                              ATTR_MAX_TEMP, ATTR_MIN_TEMP,
                                              ATTR_TEMPERATURE,
                                              PLATFORM_SCHEMA, STATE_AUTO,
                                              STATE_MANUAL, SUPPORT_AWAY_MODE,
                                              SUPPORT_OPERATION_MODE,
                                              SUPPORT_TARGET_HUMIDITY,
                                              SUPPORT_TARGET_TEMPERATURE,
                                              ClimateDevice)
from homeassistant.const import (ATTR_TEMPERATURE, CONF_HOST, CONF_PASSWORD,
                                 CONF_USERNAME, PRECISION_HALVES, TEMP_CELSIUS)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.entity import Entity

#TODO: set up requirements
REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'innogy'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

INNOGY_COMPONENTS = [
    #'sensor', 
    'climate'
]

PLATFORM_SCHEMA  = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    #TODO: Get configuration
    #username = config[DOMAIN][CONF_USERNAME]
    #password = config[DOMAIN][CONF_PASSWORD]

    from innopy.innopy_client import InnopyClient
    import json

    try:
        json_token = '{"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkxQajZ1bjFQMFh6blNuYnZXSXgxTHJFemJmUSJ9.eyJjbGllbnRfaWQiOiIyNDYzNTc0OCIsInN1YiI6ImZrcmVicyIsImRldmljZSI6IjkxNDEwMTAxNjgyNCIsImNsaWVudF9wZXJtaXNzaW9ucyI6IkRGRiIsInN0b3JlX2FjY291bnQiOiJma3JlYnNAbnVjbGkuZGUiLCJ0ZW5hbnQiOiJSV0UiLCJ1c2VyX3Blcm1pc3Npb25zIjoiRkZGRkZGRkZGRkZGRkZGRiIsInNlc3Npb24iOiJkZWYyZDUxZGFiNWY0MjE0ODFiNGI5YjVkYjhlZWY1NyIsImlzcyI6IlNtYXJ0SG9tZUFQSSIsImF1ZCI6ImFsbCIsImV4cCI6MTUyNTA5NjU1MywibmJmIjoxNTI0OTIzNzUzfQ.Zx0b807uvR6Bq_q2HVdxz3am_GoV7u6GUebFBBewjyhA0ahWZmRM0K3Yn8LPQQ_I2I0ClZy_PrPCzM5VH_lAD45Gi5bLCpxlDWuq1-vdBfU9DBFQ6VU5yQW_qH1UGb6ccRWfs3GgpneRFbZ2alK2oFRnyx9a9hCnOQ8g4tg3REmXnG_uvktH5qiUmyg4KFwE-rEruUQz9QZhPIx_GNAul5vcqkFbcA8V9A30uYDK7wV5i6W1NsLXCff03uv7NHWLkpSUEgSGOsipYq4_9nRyVTAP-UFpn4ubW_euGU4wREiYLT85IPS-PV--4gSgm_Go6vm0CFB7PX_A4t2oCxgRBA", "token_type": "Bearer", "expires_in": 172800, "refresh_token": "79281c817ebe43c4b862abfb3fceaeb9", "expires_at": 1525096597.1986635}'
        token = json.loads(json_token)
        innopy = InnopyClient(token)
        
    except Exception as e:
        _LOGGER.error("Innopy could not be initalized: " + str(e))
        return False
    
    _LOGGER.warning("getting climate devices")
    climate_devices = [InnogyThermostat(innogy_device) for innogy_device in innopy.thermostats]
    _LOGGER.warning("adding climate devices" + str(climate_devices))
    if climate_devices:
        add_devices(climate_devices, True)
    
    # sensor_devices = list()
    # for innogy_device in innopy.thermostats:
    #    for sensor_type in CLIMATE_SENSOR_TYPES:
    #        sensor_devices.append(InnogySensor(innogy_device,sensor_type))
    # if sensor_devices:
    #    add_devices(sensor_devices,True)


    _LOGGER.error("creating subscription")
    hass.async_create_task(innopy.subscribe_events())

    _LOGGER.warning("init complete")
    return True

CONST_OVERLAY_MANUAL = 'Manu'
CONST_OVERLAY_AUTOMATIC = 'Auto'

OPERATION_LIST = {
          CONST_OVERLAY_MANUAL: STATE_MANUAL,
          CONST_OVERLAY_AUTOMATIC: STATE_AUTO
        }

CLIMATE_SENSOR_TYPES = [
    #"Temperature",
    "Humidity"
    ]

class InnogyThermostat(ClimateDevice):

    def __init__(self, innogy_device):
        self._innogy_device = innogy_device
        self._support_flags = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE)
        self._min_temp = 6.0
        self._max_temp = 30.0

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        mode = self._innogy_device.capabilities_dict["OperationMode"]["value"]
        return OPERATION_LIST.get(mode)

    @property
    def unique_id(self):
        """Unique ID for this device."""
        return self._innogy_device.id

    @property
    def name(self):
        """Return the name of the device."""
        return self._innogy_device.config_dict["Name"]
    
    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._innogy_device.capabilities_dict["Humidity"]["value"]
    
    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._innogy_device.capabilities_dict["Temperature"]["value"]
    
    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._innogy_device.capabilities_dict["PointTemperature"]["value"]

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return PRECISION_HALVES
    
    @property
    def operation_list(self):
        """List of available operation modes."""
        return list(OPERATION_LIST.values())

    @property
    def available(self):
        """Return if thermostat is available."""
        return self._innogy_device.device_state_dict["IsReachable"]["value"]


    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {
            ATTR_CURRENT_HUMIDITY: self._innogy_device.capabilities_dict["Humidity"]["value"],
            "is_reachable": self._innogy_device.device_state_dict["IsReachable"]["value"],
            #TODO: implement battery low message handling
            #ATTR_STATE_BATTERY_LOW: self._device.battery_low
        }
        return attrs


    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._min_temp:
            return self._min_temp
        # get default temp from super class
        return super().min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._max_temp:
            return self._max_temp
        #  Get default temp from super class
        return super().max_temp

    def update(self):
        """Update the state of this climate device."""
        #This is handled by the websocket
        pass

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.warn("set temp: " + str(temperature))
        if temperature is None:
            return
        self._innogy_device.client.set_PointTemperature_state(
            self._innogy_device.capabilities_dict["PointTemperature"]["id"],float(temperature))


    # pylint: disable=arguments-differ
    def set_operation_mode(self, readable_operation_mode):
        """Set new operation mode."""
        _LOGGER.warn("set mode: " + str(readable_operation_mode))
        if readable_operation_mode == "Automatic":
            self._innogy_device.client.set_OperationMode_state(
                self._innogy_device.capabilities_dict["OperationMode"]["id"],True)
        else:
            self._innogy_device.client.set_OperationMode_state(
                self._innogy_device.capabilities_dict["OperationMode"]["id"],False)


class InnogySensor(Entity):
    """Representation of a tado Sensor."""

    def __init__(self, innogy_device, sensor_type):
        """Initialize of the Innogy Sensor."""
        self._innogy_device = innogy_device
        self._sensor_type = sensor_type
        self._state = None
        self._state_attributes = None

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._innogy_device.capabilities_dict[self._sensor_type]["id"]+str(self._sensor_type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._innogy_device.config_dict["Name"] +"_"+ self._sensor_type

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._sensor_type == "Temperature":
            return TEMP_CELSIUS
        elif self._sensor_type == "Humidity":
            return '%'

    @property
    def icon(self):
        """Icon for the sensor."""
        if self._sensor_type == "Temperature":
            return 'mdi:thermometer'
        elif self._sensor_type == "Humidity":
            return 'mdi:water-percent'

    def update(self):
        """Update method called when should_poll is true."""
        self._state = innogy_device.capabilities_dict[self._sensor_type]["value"]
        

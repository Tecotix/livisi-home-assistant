"""Define support for Eufy Security devices."""
from datetime import timedelta
import logging

from hass_livisi import async_login
from hass_livisi.errors import HassLivisiError, InvalidCredentialsError
import voluptuous as vol

from innopy.innopy_client import InnopyClient
    import json

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client, config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .config_flow import configured_instances
from .const import DATA_API, DATA_LISTENER, DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the Hass Livisi component."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DATA_API] = {}
    hass.data[DOMAIN][DATA_LISTENER] = {}

    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    if conf[CONF_USERNAME] in configured_instances(hass):
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_USERNAME: conf[CONF_USERNAME],
                CONF_PASSWORD: conf[CONF_PASSWORD],
            },
        )
    )

    return True


async def async_setup_entry(hass, config_entry):
    """Set up Hass Livisi as a config entry."""
     session = aiohttp_client.async_get_clientsession(hass)

    # try:
        # api = await async_login(
            # config_entry.data[CONF_USERNAME], config_entry.data[CONF_PASSWORD], session
        # )
    # except InvalidCredentialsError:
        # _LOGGER.error("Invalid username and/or password")
        # return False
    # except HassLivisiError as err:
        # _LOGGER.error("Config entry failed: %s", err)
        # raise ConfigEntryNotReady

    # hass.data[DOMAIN][DATA_API][config_entry.entry_id] = api

    # hass.async_create_task(
        # hass.config_entries.async_forward_entry_setup(config_entry, "livisi")
    # )

    # async def refresh(event_time):
        # """Refresh data from the API."""
        # _LOGGER.debug("Refreshing API data")
        # await api.async_update_device_info()

    # hass.data[DOMAIN][DATA_LISTENER][config_entry.entry_id] = async_track_time_interval(
        # hass, refresh, DEFAULT_SCAN_INTERVAL
    # )

    # return True
    
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


async def async_unload_entry(hass, config_entry):
    """Unload a Eufy Security config entry."""
    hass.data[DOMAIN][DATA_API].pop(config_entry.entry_id)
    cancel = hass.data[DOMAIN][DATA_LISTENER].pop(config_entry.entry_id)
    cancel()

    await hass.config_entries.async_forward_entry_unload(config_entry, "livisi")

    return True
    
    
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
        

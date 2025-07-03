from .taichuan_entity import TaichuanEntity
from .taichuan.core.device import TaichuanDevice
from .taichuan.devices.x06.device import Taichuan06Device
from .taichuan_device import TAICHUAN_DEVICES
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    LightEntityFeature,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_MIN_COLOR_TEMP_KELVIN,
    ATTR_MAX_COLOR_TEMP_KELVIN,
)
from .taichuan_device import X06Attributes
from .taichuan.core.cloud import UCloud
from .taichuan.devices.__init__ import device_selector
import threading
import json
import asyncio
import logging
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_SWITCHES
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.util.json import load_json
from .const import (
    DOMAIN,
    EXTRA_SENSOR,
    EXTRA_CONTROL,
    CONF_ACCOUNT,
    CONF_SERVER,
    CONF_KEY,
    CONF_MODEL,
    CONF_DEVTYPE,
    CONF_REFRESH_INTERVAL
)

from homeassistant.const import (
    CONF_NAME,
    CONF_DEVICE,
    CONF_TOKEN,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_SWITCHES,
    CONF_SENSORS,
    CONF_CUSTOMIZE,
    CONF_PASSWORD,
)
_LOGGER = logging.getLogger(__name__)
from .const import (
    DOMAIN,
    DEVICES,
)

clouds = {
    "珠海U家": {
        "class_name": "UCloud",
        "api_url": "https://ucloud.taichuan.net",
    }
}
from .taichuan.core.cloud import get_taichuan_cloud
from .hub import Taichuanhub
STORAGE_PATH = f".storage/{DOMAIN}"

""" def load_account:
        record_file = self.hass.config.path(f"{STORAGE_PATH}/account.json")
        json_data = load_json(record_file, default={})
        if CONF_ACCOUNT in json_data.keys():
            json_data[CONF_PASSWORD] = bytes.fromhex(format((
                    int(json_data[CONF_PASSWORD], 16) ^
                    int(json_data[CONF_ACCOUNT].encode("utf-8").hex(), 16)), 'X')
            ).decode('UTF-8')
        return json_data
 """    


def load_account(hass):
    record_file = hass.config.path(f"{STORAGE_PATH}/account.json")
    json_data = load_json(record_file, default={})
    if CONF_ACCOUNT in json_data.keys():
        json_data[CONF_PASSWORD] = bytes.fromhex(format((
            int(json_data[CONF_PASSWORD], 16) ^
            int(json_data[CONF_ACCOUNT].encode("utf-8").hex(), 16)), 'X')
        ).decode('UTF-8')
        return json_data
    
async def async_setup_entry(hass, config_entry, async_add_entities):
    taichuan_hub = hass.data[DOMAIN][config_entry.entry_id]
    if taichuan_hub is None:
        json_data = load_account(hass)
        if not json_data or "server" not in json_data or "account" not in json_data or "password" not in json_data:
            _LOGGER.error("Missing required account data in account.json")
            return False
            
        cloud_name = json_data.get("server", "")
        username = json_data.get("account", "")
        password = json_data.get("password", "")
        session = async_create_clientsession(hass)
        
        cloud = get_taichuan_cloud(
                    cloud_name,
                    session,
                    username,
                    password,
                )
        taichuan_hub = Taichuanhub(cloud)
        await taichuan_hub._ucloud.login()

    devs = []
    devices = await taichuan_hub.get_devices()
    for device_id,device in devices.items():
        if device is not None and device.device_type in TAICHUAN_DEVICES:
            device_config = TAICHUAN_DEVICES[device.device_type]
            for entity_key, config in device_config.get("entities", {}).items():
                if config["type"] == Platform.LIGHT:
                    dev = TaichuanLight(device, entity_key, taichuan_hub)
                    devs.append(dev)
    
    async_add_entities(devs)


class TaichuanLight(TaichuanEntity,LightEntity):
    def __init__(self,device,entity_key,cloud):
        super().__init__(device, entity_key)
        self._cloud = cloud 
        self._device = device
   
    @property
    def is_on(self):
        return self._device.get_attribute(X06Attributes.power)

    @property
    def supported_features(self) -> LightEntityFeature:
        return LightEntityFeature.EFFECT

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        return {ColorMode.ONOFF}

    async def async_turn_on(self, **kwargs):
        if not self.is_on:
            self._device.set_attribute(attr=X06Attributes.power, value=True)
            await self._cloud.dev_opt(self._device.device_type, self._device.device_id, True)

    async def async_turn_off(self, **kwargs):
        self._device.set_attribute(attr=X06Attributes.power, value=False)
        await self._cloud.dev_opt(self._device.device_type, self._device.device_id, False)

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            _LOGGER.debug(f"Entity {self.entity_id} update_state {repr(e)}, status = {status}")
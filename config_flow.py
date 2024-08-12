import voluptuous as vol
from .hub import Taichuanhub
import os
import json
try:
    from homeassistant.helpers.json import save_json
except ImportError:
    from homeassistant.util.json import save_json
from homeassistant.util.json import load_json
import logging
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
from homeassistant import config_entries
from homeassistant.core import callback
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
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .taichuan.core.discover import discover
from .taichuan.core.cloud import get_taichuan_cloud
from .taichuan.core.cloud import UCloud
from .taichuan.core.device import TaichuanDevice
from .taichuan_device import TAICHUAN_DEVICES

from .taichuan.devices import device_selector

_LOGGER = logging.getLogger(__name__)

ADD_WAY = {'device': 'scan devices', 'scene': 'scan scenes'}
STORAGE_PATH = f".storage/{DOMAIN}"

SERVERS = {
    1: "珠海U家",
    2: "珠海U家[测试]",
    3: "东莞智慧社区云平台",
    4: "兰州U家",
    5: "天翼平台",
}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    available_device = []
    available_scene = []
    devices = {}
    found_device = {}
    scenes = {}
    found_scenes={}
    supports = {}
    unsorted = {}
    account = {}
    cloud = None
    session = None
    for device_type, device_info in TAICHUAN_DEVICES.items():
        unsorted[device_type] = device_info["name"]

    unsorted = sorted(unsorted.items(), key=lambda x: x[1])
    for item in unsorted:
        supports[item[0]] = item[1]

    def _save_device_config(self, data: dict):
        os.makedirs(self.hass.config.path(STORAGE_PATH), exist_ok=True)
        record_file = self.hass.config.path(f"{STORAGE_PATH}/{data[CONF_DEVICE_ID]}.json")
        save_json(record_file, data)

    def _load_device_config(self, device_id):
        record_file = self.hass.config.path(f"{STORAGE_PATH}/{device_id}.json")
        json_data = load_json(record_file, default={})
        return json_data

    def _save_account(self, account: dict):
        os.makedirs(self.hass.config.path(STORAGE_PATH), exist_ok=True)
        record_file = self.hass.config.path(f"{STORAGE_PATH}/account.json")
        account[CONF_PASSWORD] = format((int(account[CONF_ACCOUNT].encode("utf-8").hex(), 16) ^
                                         int(account[CONF_PASSWORD].encode("utf-8").hex(), 16)), 'x')
        save_json(record_file, account)

    def _load_account(self):
        record_file = self.hass.config.path(f"{STORAGE_PATH}/account.json")
        json_data = load_json(record_file, default={})
        if CONF_ACCOUNT in json_data.keys():
            json_data[CONF_PASSWORD] = bytes.fromhex(format((
                    int(json_data[CONF_PASSWORD], 16) ^
                    int(json_data[CONF_ACCOUNT].encode("utf-8").hex(), 16)), 'X')
            ).decode('UTF-8')
        return json_data

    @staticmethod
    def _check_storage_device(device: dict, storage_device: dict):
        if storage_device.get(CONF_DEVTYPE) is None:
            return False
        return True

    def _already_configured(self, device_id):
        for entry in self._async_current_entries():
            if device_id == entry.data.get(CONF_DEVICE_ID):
                return True
        return False

    async def async_step_user(self, user_input=None, error=None):
        if user_input is not None:
            if self.session is None:
                self.session = async_create_clientsession(self.hass)


            if self.cloud is None:
                self.cloud = get_taichuan_cloud(
                    session=self.session,
                    cloud_name=SERVERS[user_input[CONF_SERVER]],
                    username=user_input[CONF_ACCOUNT],
                    password=user_input[CONF_PASSWORD]
                )

            if await self.cloud.login():
                self.account = {
                    CONF_ACCOUNT: user_input[CONF_ACCOUNT],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_SERVER:  SERVERS[user_input[CONF_SERVER]]
                }

                self._save_account(self.account)
                #return self.async_create_entry(title=user_input[CONF_ACCOUNT],data=data_info)
                return await self.async_step_discovery()
            else:
                return await self.async_step_user(error="login_failed")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ACCOUNT): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SERVER, default=1): vol.In(SERVERS)
            }),
            errors={"base": error} if error else None
        )

    async def async_step_discovery(self, user_input=None, error=None):
        if user_input is not None:
            taichuan_hub = Taichuanhub(self.cloud)
            data_info={}
            data_info[user_input["action"]] = taichuan_hub
            return self.async_create_entry(title=user_input["action"],data=data_info)

        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema({
                vol.Required("action", default="discovery"): vol.In(ADD_WAY)
            }),
            errors={"base": error} if error else None
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self._config_entry = config_entry
        self._device_type = config_entry.data.get(CONF_TYPE)
        if self._device_type is None:
            self._device_type = 0xac
        if CONF_SENSORS in self._config_entry.options:
            for key in self._config_entry.options[CONF_SENSORS]:
                if key not in TAICHUAN_DEVICES[self._device_type]["entities"]:
                    self._config_entry.options[CONF_SENSORS].remove(key)
        if CONF_SWITCHES in self._config_entry.options:
            for key in self._config_entry.options[CONF_SWITCHES]:
                if key not in TAICHUAN_DEVICES[self._device_type]["entities"]:
                    self._config_entry.options[CONF_SWITCHES].remove(key)

    async def async_step_init(self, user_input=None):
        if self._device_type == CONF_ACCOUNT:
            return self.async_abort(reason="account_option")
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        sensors = {}
        switches = {}
        for attribute, attribute_config in TAICHUAN_DEVICES.get(self._device_type).get("entities").items():
            attribute_name = attribute if type(attribute) is str else attribute.value
            if attribute_config.get("type") in EXTRA_SENSOR:
                sensors[attribute_name] = attribute_config.get("name")
            elif attribute_config.get("type") in EXTRA_CONTROL and not attribute_config.get("default"):
                switches[attribute_name] = attribute_config.get("name")
        
        refresh_interval = self._config_entry.options.get(
            CONF_REFRESH_INTERVAL, 30
        )
        extra_sensors = list(set(sensors.keys()) & set(self._config_entry.options.get(
            CONF_SENSORS, []
        )))
        extra_switches = list(set(switches.keys()) & set(self._config_entry.options.get(
            CONF_SWITCHES, []
        )))
        customize = self._config_entry.options.get(
            CONF_CUSTOMIZE, ""
        )
        data_schema = vol.Schema({
            vol.Required(
                CONF_REFRESH_INTERVAL,
                default=refresh_interval
            ): int
        })
        if len(sensors) > 0:
            data_schema = data_schema.extend({
                vol.Required(
                    CONF_SENSORS,
                    default=extra_sensors,
                ):
                    cv.multi_select(sensors)
            })
        if len(switches) > 0:
            data_schema = data_schema.extend({
                vol.Required(
                    CONF_SWITCHES,
                    default=extra_switches,
                ):
                    cv.multi_select(switches)
            })
        data_schema = data_schema.extend({
            vol.Optional(
                CONF_CUSTOMIZE,
                default=customize,
            ):
                str
        })

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_ACCOUNT): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SERVER, default=1): vol.In(SERVERS)
            }),
            errors={"base": error} if error else None
        )
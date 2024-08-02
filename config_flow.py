import voluptuous as vol
import os
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
from .taichuan.core.device import TaichuanDevice
from .taichuan_device import TAICHUAN_DEVICES

_LOGGER = logging.getLogger(__name__)

#ADD_WAY = {"discovery": "Discover automatically", "manually": "Configure manually", "list": "List all appliances only"}
ADD_WAY = {'device': 'scan devices', 'scene': 'scan scenes'}
PROTOCOLS = {1: "V1", 2: "V2", 3: "V3"}
STORAGE_PATH = f".storage/{DOMAIN}"

SERVERS = {
    1: "珠海U家",
    2: "珠海U家[测试]",
    3: "东莞智慧社区云平台",
    4: "兰州U家",
    5: "天翼平台",
}

PRESET_ACCOUNT = [
    39182118275972017797890111985649342047468653967530949796945843010512,
    29406100301096535908214728322278519471982973450672552249652548883645,
    39182118275972017797890111985649342050088014265865102175083010656997
]


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
        #if (device.get(CONF_PROTOCOL) == 3 and
        #        (storage_device.get(CONF_TOKEN) is None or storage_device.get(CONF_KEY) is None)):
        #    return False
        return True

    #def _already_configured(self, device_id, ip_address):
    def _already_configured(self, device_id):
        for entry in self._async_current_entries():
            #if device_id == entry.data.get(CONF_DEVICE_ID) or ip_address == entry.data.get(CONF_IP_ADDRESS):
            if device_id == entry.data.get(CONF_DEVICE_ID):
                return True
        return False

    """ async def async_step_user(self, user_input=None, error=None):
        if user_input is not None:
            if user_input["action"] == "discovery":
                return await self.async_step_discovery()
            elif user_input["action"] == "manually":
                self.found_device = {}
                return await self.async_step_manually()
            else:
                return await self.async_step_list()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("action", default="discovery"): vol.In(ADD_WAY)
            }),
            errors={"base": error} if error else None
        ) """

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
                return await self.async_step_discovery()
            else:
                return await self.async_step_login(error="login_failed")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ACCOUNT): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SERVER, default=1): vol.In(SERVERS)
            }),
            errors={"base": error} if error else None
        )

    async def async_step_list(self, user_input=None, error=None):
        #添加自己的设备发现方式
        if user_input is not None:
            #_LOGGER.info(f"user_input[{user_input[CONF_DEVICE]}]")
            #all_devices = self.available_device

            _LOGGER.info(f"avaliable_devices[]")
        else:
            if len(self.devices) > 0:
                table = "Appliance code|Type|ID|Supported\n:--:|:--:|:--:|:--:"
                for device in self.devices:
                    supported = device.get(CONF_DEVTYPE) in self.supports.keys()
                    table += f"\n{'%02X' % device.get(CONF_DEVTYPE)} | {device.get(CONF_DEVTYPE)}|{device.get('id')}|{'<font color=gree>YES</font>' if supported else '<font color=red>NO</font>'}"
            else:
                table = "Not found"

            return self.async_show_form(
                step_id="list",
                data_schema=vol.Schema({
                    vol.Required(CONF_DEVICE, default="device"):
                        vol.In(list(table)),
                }),
                errors={"base": error} if error else None
            )
    async def async_step_discovery(self, user_input=None, error=None):
        if user_input is not None:
            if user_input["action"] == "device":
                self.devices = await self.cloud.list_dev()
                self.available_device = {}
                for device in self.devices:
                    device_id = device.get("id")
                    if not self._already_configured(device_id):
                        self.available_device[device_id] = f"{device_id} ({self.supports.get(device.get(CONF_DEVTYPE))})"

                if(len(self.available_device)>0):
                    return await self.async_step_list()
                else:
                    return await self.async_step_discovery(error="no device found")
            elif user_input["actioin"] == "scene":
                scenes = self.cloud.list_scene()
                self.scenes = self.cloud.list_scene()
                self.available_scene ={}
                if(len(self.available_scene)>0):
                    return await self.async_step_list()
                else:
                    return await self.async_step_discovery(error="no  scene found")
        _LOGGER.info(f"ADD_WAY{ADD_WAY}")
        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema({
                #vol.Required(CONF_IP_ADDRESS, default="auto"): str
                vol.Required("action", default="discovery"): vol.In(ADD_WAY)
            }),
            errors={"base": error} if error else None
        )

    async def async_step_auto(self, user_input=None, error=None):
        if user_input is not None:
            device_id = user_input[CONF_DEVICE]
            device = self.devices.get(device_id)
            storage_device = self._load_device_config(device_id)
            if self._check_storage_device(device, storage_device):
                self.found_device = {
                    CONF_DEVICE_ID: device_id,
                    CONF_TYPE: device.get(CONF_TYPE),
                    CONF_MODEL: device.get(CONF_MODEL),
                    CONF_NAME: storage_device.get(CONF_NAME),
                    CONF_DEVTYPE: storage_device.get(CONF_DEVTYPE),
                    CONF_TOKEN: storage_device.get(CONF_TOKEN),
                    CONF_KEY: storage_device.get(CONF_KEY)
                }
                _LOGGER.info(f"Loaded configuration for device {device_id} from storage")
                return await self.async_step_manually()
            else:
                if CONF_ACCOUNT not in self.account.keys():
                    self.account = self._load_account()
                    if CONF_ACCOUNT not in self.account.keys():
                        return await self.async_step_login()
                if self.session is None:
                    self.session = async_create_clientsession(self.hass)
                if self.cloud is None:
                    self.cloud = get_taichuan_cloud(
                        self.account[CONF_SERVER], 
                        self.session, 
                        self.account[CONF_ACCOUNT],
                        self.account[CONF_PASSWORD])
                if not await self.cloud.login():
                    return await self.async_step_login()
                self.found_device = {
                    CONF_DEVICE_ID: device_id,
                    CONF_TYPE: device.get(CONF_TYPE),
                    CONF_MODEL: device.get(CONF_MODEL),
                }
                if device_info := await self.cloud.get_device_info(device_id):
                    self.found_device[CONF_NAME] = device_info.get("name")
                    self.found_device[CONF_DEVTYPE] = device_info.get("devType")
                """ if device.get(CONF_PROTOCOL) == 3:
                    if self.account[CONF_SERVER] == "美的美居":
                        _LOGGER.info(f"Try to get the Token and the Key use the preset MSmartHome account")
                        self.cloud = get_taichuan_cloud(
                            "MSmartHome",
                            self.session,
                            bytes.fromhex(format((PRESET_ACCOUNT[0] ^ PRESET_ACCOUNT[1]), 'X')).decode('ASCII'),
                            bytes.fromhex(format((PRESET_ACCOUNT[0] ^ PRESET_ACCOUNT[2]), 'X')).decode('ASCII'))
                        if not await self.cloud.login():
                            return await self.async_step_auto(error="preset_account")
                    keys = await self.cloud.get_keys(user_input[CONF_DEVICE])
                    for method, key in keys.items():
                        dm = TaichuanDevice(
                            name="",
                            device_id=device_id,
                            device_type=device.get(CONF_TYPE),
                            ip_address=device.get(CONF_IP_ADDRESS),
                            port=device.get(CONF_PORT),
                            token=key["token"],
                            key=key["key"],
                            protocol=3,
                            model=device.get(CONF_MODEL),
                            subtype=0,
                            attributes={}
                        )
                        if dm.connect(refresh_status=False):
                            dm.close_socket()
                            self.found_device[CONF_TOKEN] = key["token"]
                            self.found_device[CONF_KEY] = key["key"]
                            return await self.async_step_manually()
                    return await self.async_step_auto(error="connect_error")
                else: """
                return await self.async_step_manually()

        return self.async_show_form(
            step_id="auto",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE, default=list(self.available_device.keys())[0]):
                    vol.In(self.available_device),
            }),
            errors={"base": error} if error else None
        )

    async def async_step_manually(self, user_input=None, error=None):
        if user_input is not None:
            self.found_device = {
                CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                CONF_TYPE: user_input[CONF_TYPE],
                CONF_MODEL: user_input[CONF_MODEL],
                CONF_TOKEN: user_input[CONF_TOKEN],
                CONF_KEY: user_input[CONF_KEY]
            }
            try:
                bytearray.fromhex(user_input[CONF_TOKEN])
                bytearray.fromhex(user_input[CONF_KEY])
            except ValueError:
                return await self.async_step_manually(error="invalid_token")
            #if user_input[CONF_PROTOCOL] == 3 and (len(user_input[CONF_TOKEN]) == 0 or len(user_input[CONF_KEY]) == 0):
            #    return await self.async_step_manually(error="invalid_token")
            dm = TaichuanDevice(
                name="",
                device_id=user_input[CONF_DEVICE_ID],
                device_type=user_input[CONF_TYPE],
                token=user_input[CONF_TOKEN],
                key=user_input[CONF_KEY],
                model=user_input[CONF_MODEL],
                subtype=0,
                attributes={}
            )
            if dm.connect(refresh_status=False):
                dm.close_socket()
                data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                    CONF_TYPE: user_input[CONF_TYPE],
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_DEVTYPE: user_input[CONF_DEVTYPE],
                    CONF_TOKEN: user_input[CONF_TOKEN],
                    CONF_KEY: user_input[CONF_KEY],
                    }
                self._save_device_config(data)
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]}",
                    data=data
                )
            else:
                return await self.async_step_manually(error="config_incorrect")
        return self.async_show_form(
            step_id="manually",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_NAME,
                    default=(self.found_device.get(CONF_NAME)
                             if self.found_device.get(CONF_NAME)
                             else self.supports.get(self.found_device.get(CONF_TYPE)))
                ): str,
                vol.Required(
                    CONF_DEVICE_ID,
                    default=self.found_device.get(CONF_DEVICE_ID)
                ): int,
                vol.Required(
                    CONF_TYPE,
                    default=self.found_device.get(CONF_TYPE) if self.found_device.get(CONF_TYPE) else 0xac
                ): vol.In(self.supports),
                vol.Required(
                    CONF_MODEL,
                    default=self.found_device.get(CONF_MODEL) if self.found_device.get(CONF_MODEL) else "Unknown"
                ): str,
                vol.Required(
                    CONF_DEVTYPE,
                    default=self.found_device.get(CONF_DEVTYPE) if self.found_device.get(CONF_DEVTYPE) else 0
                ): int,
                vol.Optional(
                    CONF_TOKEN,
                    default=self.found_device.get(CONF_TOKEN) if self.found_device.get(CONF_TOKEN) else ""
                ): str,
                vol.Optional(
                    CONF_KEY,
                    default=self.found_device.get(CONF_KEY) if self.found_device.get(CONF_KEY) else ""
                ): str,
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
            data_schema=data_schema
        )

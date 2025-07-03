import logging
import voluptuous as vol
from .hub import Taichuanhub
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .taichuan.core.cloud import get_taichuan_cloud
from .const import (
    DOMAIN,
    CONF_ACCOUNT,
    CONF_KEY,
    CONF_MODEL,
    CONF_DEVTYPE,
    CONF_REFRESH_INTERVAL,
    DEVICES,
    EXTRA_SENSOR,
    EXTRA_SWITCH,
    EXTRA_CONTROL,
    ALL_PLATFORM,
)
from .taichuan_device import TAICHUAN_DEVICES

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_NAME,
    CONF_TOKEN,
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_DEVICE_ID,
    CONF_TYPE,
    CONF_CUSTOMIZE,
)
from .taichuan.devices.__init__ import device_selector

_LOGGER = logging.getLogger(__name__)


async def update_listener(hass, config_entry):
    for platform in ALL_PLATFORM:
        await hass.config_entries.async_forward_entry_unload(config_entry, platform)
    for platform in ALL_PLATFORM:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(
            config_entry, platform))
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    customize = config_entry.options.get(
        CONF_CUSTOMIZE, ""
    )
    ip_address = config_entry.options.get(
        CONF_IP_ADDRESS, None
    )
    refresh_interval = config_entry.options.get(
        CONF_REFRESH_INTERVAL, None
    )
    dev = hass.data[DOMAIN][DEVICES].get(device_id)
    if dev:
        dev.set_customize(customize)
        if ip_address is not None:
            dev.set_ip_address(ip_address)
        if refresh_interval is not None:
            dev.set_refresh_interval(refresh_interval)


async def async_setup(hass: HomeAssistant, hass_config: dict):
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry):  # noqa: D103
    if DOMAIN not in hass.data:
        hass.data[DOMAIN]={}
    if DEVICES not in hass.data[DOMAIN]:
        hass.data[DOMAIN][DEVICES] = {}

    # 使用配置条目中的信息创建Taichuanhub实例
    action = config_entry.data.get("action")
    if action in ("device", "scene"):
        session = async_create_clientsession(hass)
        cloud = get_taichuan_cloud(
            session=session,
            cloud_name=config_entry.data.get("server"),
            username=config_entry.data.get("account"),
            password=config_entry.data.get("password")
        )
        
        # 创建Taichuanhub实例
        taichuan_hub = Taichuanhub(cloud)
        
        # 存储实例到hass.data中
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = taichuan_hub

    await hass.config_entries.async_forward_entry_setups(config_entry, ALL_PLATFORM)
    config_entry.add_update_listener(update_listener)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry):
    return True
    device_type = config_entry.data.get(CONF_DEVTYPE)
    #if device_type == CONF_ACCOUNT:
    #    return True
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    if device_id is not None:
        dm = hass.data[DOMAIN][DEVICES].get(device_id)
        if dm is not None:
            dm.close()
        hass.data[DOMAIN][DEVICES].pop(device_id)
    for platform in ALL_PLATFORM:
        await hass.config_entries.async_forward_entry_unload(config_entry, platform)
    return True
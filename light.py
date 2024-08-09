from .taichuan_entity import TaichuanEntity
from .taichuan.core.device import TaichuanDevice
from .taichuan.devices.x06.device import Taichuan06Device
from .taichuan_device import TAICHUAN_DEVICES
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.components.light import *
from .taichuan_device import X06Attributes
from .taichuan.core.cloud import UCloud
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_SWITCHES
)

from .const import (
    DOMAIN,
    DEVICES,
)

async def async_setup_entry(hass, config_entry, async_add_entities):
    devs = []
    for device_id,device in hass.data[DOMAIN][DEVICES].items():
        if device is not None and device.device_type==6:
            for entity_key, config in TAICHUAN_DEVICES[device.device_type]["entities"].items():
                if config["type"] == Platform.LIGHT:
                    dev = TaichuanLight(device,entity_key)
                    devs.append(dev)
    async_add_entities(devs)


class TaichuanLight(TaichuanEntity,LightEntity):
    def __init__(self, device,entity_key):
        super().__init__(device, entity_key)
    
    @property
    def is_on(self):
        return self._device.get_attribute(X06Attributes.power)

    #@property
    #def cloud(self):
    #    return self._cloud

    #@property
    #def effect(self):
    #    return self._device.get_attribute(X06Attributes.effect)
    
    @property
    def supported_features(self) -> LightEntityFeature:
        supported_features = LightEntityFeature(SUPPORT_EFFECT)
        return supported_features

    @property
    def supported_color_modes(self)->ColorMode:
        supported_color_modes = ColorMode(COLOR_MODE_ONOFF)
        return supported_color_modes

    def turn_on(self):
        if not self.is_on:
            self._device.set_attribute(attr=X06Attributes.power, value=True)
    #        self._cloud.dev_opt(self._device.device_type,self._device.device_id,True)
    
    def turn_off(self):
        self._device.set_attribute(attr=X06Attributes.power, value=False)
    #    self._cloud.dev_opt(self._device.device_type,self._device.device_id,False)

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            _LOGGER.debug(f"Entity {self.entity_id} update_state {repr(e)}, status = {status}")
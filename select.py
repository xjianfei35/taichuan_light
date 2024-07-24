from .taichuan_entity import TaichuanEntity
from .taichuan_device import TAICHUAN_DEVICES
from homeassistant.components.select import SelectEntity
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
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_switches = config_entry.options.get(
        CONF_SWITCHES, []
    )
    selects = []
    for entity_key, config in TAICHUAN_DEVICES[device.device_type]["entities"].items():
        if config["type"] == Platform.SELECT and entity_key in extra_switches:
            dev = TaichuanSelect(device, entity_key)
            selects.append(dev)
    async_add_entities(selects)


class TaichuanSelect(TaichuanEntity, SelectEntity):
    def __init__(self, device, entity_key: str):
        super().__init__(device, entity_key)
        self._options_name = self._config.get("options")

    @property
    def options(self):
        return getattr(self._device, self._options_name)

    @property
    def current_option(self):
        return self._device.get_attribute(self._entity_key)

    def select_option(self, option: str):
        self._device.set_attribute(self._entity_key, option)

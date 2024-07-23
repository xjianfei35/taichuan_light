from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import Platform, CONF_DEVICE_ID, CONF_SENSORS
from .const import (
    DOMAIN,
    DEVICES
)
from .taichuan_entity import TaichuanEntity
from .taichuan_devices import TAICHUAN_DEVICES


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_sensors = config_entry.options.get(
        CONF_SENSORS, []
    )
    binary_sensors = []
    for entity_key, config in TAICHUAN_DEVICES[device.device_type]["entities"].items():
        if config["type"] == Platform.BINARY_SENSOR and entity_key in extra_sensors:
            sensor = TaichuanSensor(device, entity_key)
            binary_sensors.append(sensor)
    async_add_entities(binary_sensors)


class TaichuanSensor(TaichuanEntity, BinarySensorEntity):
    @property
    def device_class(self):
        return self._config.get("device_class")

    @property
    def is_on(self):
        return self._device.get_attribute(self._entity_key)

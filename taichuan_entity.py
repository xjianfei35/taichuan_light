from homeassistant.helpers.entity import Entity
from .const import DOMAIN
from .taichuan_device import TAICHUAN_DEVICES

import logging
_LOGGER = logging.getLogger(__name__)


class TaichuanEntity(Entity):
    def __init__(self, device,entity_key: str):
        self._device = device
        self._config = TAICHUAN_DEVICES[self._device.device_type]["entities"][entity_key]
        self._entity_key = entity_key
        self._device_name = self._device.device_name
        _attr_unique_id = f"{self._device.device_name}{self._device.device_type}{self._device.device_id}" 
    @property
    def device(self):
        return self._device

    @property
    def device_info(self):
        return {
            "manufacturer": "Taichuan",
            "model": f"{TAICHUAN_DEVICES[self._device.device_type]['name']} "
                     f"{self._device.device_id}",
            "identifiers": {(DOMAIN, self._device.device_id)},
            "name": self._device_name
        }

    @property
    def name(self):
        return f"{self._device_name} {self._config.get('name')}" if "name" in self._config \
            else self._device_name

    def update_state(self, status):
        if self._entity_key in status or "available" in status:
            try:
                self.schedule_update_ha_state()
            except Exception as e:
                _LOGGER.info(f"Entity {self.entity_id} update_state {repr(e)}, status = {status}")

import logging
import json
from .message import (
    MessageQuery,
    MessageSet,
    Message06Response
)
try:
    from enum import StrEnum
except ImportError:
    from ...backports.enum import StrEnum
from ...core.device import TaichuanDevice
from ...core.cloud import UCloud
_LOGGER = logging.getLogger(__name__)


class DeviceAttributes(StrEnum):
    power = "power"


class Taichuan06Device(TaichuanDevice):
    _effects = ["Manual", "Living", "Reading", "Mildly", "Cinema", "Night"]

    def __init__(
            self,
            name: str,
            device_id: int,
            device_type: int,
    ):
        super().__init__(
            name=name,
            device_id=device_id,
            device_type=device_type,
            attributes={
                DeviceAttributes.power:False
            }
            )

    def set_attribute(self, attr, value): 
        if (attr == DeviceAttributes.power):
            setattr(self,DeviceAttributes.power,value) 
            
    @property
    def effects(self):
        return Taichuan06Device._effects

class TaichuanAppliance(Taichuan06Device):
    pass

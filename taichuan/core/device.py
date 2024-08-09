import threading
try:
    from enum import StrEnum
except ImportError:
    from ..backports.enum import StrEnum
from enum import IntEnum
from .security import LocalSecurity, MSGTYPE_HANDSHAKE_REQUEST, MSGTYPE_ENCRYPTED_REQUEST
from .packet_builder import PacketBuilder
from .message import (
    MessageType,
    MessageQuestCustom,
    MessageQueryAppliance,
    MessageApplianceResponse
)
import socket
import logging
import time

_LOGGER = logging.getLogger(__name__)


class AuthException(Exception):
    pass


class ResponseException(Exception):
    pass


class RefreshFailed(Exception):
    pass


class DeviceAttributes(StrEnum):
    pass


class ParseMessageResult(IntEnum):
    SUCCESS = 0
    PADDING = 1
    ERROR = 99


class TaichuanDevice():
    def __init__(self,
                 name: str,
                 device_id: int,
                 device_type: int,
                 attributes: dict):
        self._attributes = attributes if attributes else {}
        self._device_name = name
        self._device_id = device_id
        self._device_type = device_type
    
    @property
    def device_name(self):
        return self._device_name

    @property
    def device_id(self):
        return self._device_id

    @property
    def device_type(self):
        return self._device_type
    
    def attributes(self):
        ret = {}
        for status in self._attributes.keys():
            ret[str(status)] = self._attributes[status]
            return ret
        
    def set_attribute(self, attr, value):
        raise NotImplementedError

    def get_attribute(self, attr):
        raise NotImplementedError
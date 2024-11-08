""" from homeassistant.const import (
    Platform,
    TIME_DAYS,
    TIME_HOURS,
    TIME_MINUTES,
    TIME_SECONDS,
    TEMP_CELSIUS,
    POWER_WATT,
    PERCENTAGE,
    VOLUME_LITERS,
    ENERGY_KILO_WATT_HOUR,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION
) """

from homeassistant.const import(
    Platform,
)

#from homeassistant.components.binary_sensor import BinarySensorDeviceClass
#from homeassistant.components.sensor import SensorStateClass, SensorDeviceClassEASWQS
from .taichuan.devices.x06.device import DeviceAttributes as X06Attributes
""" from .taichuan.devices.x06.device import DeviceAttributes as X06Attributes
from .taichuan.devices.x34.device import DeviceAttributes as X34Attributes
from .taichuan.devices.x40.device import DeviceAttributes as X40Attributes
from .taichuan.devices.a1.device import DeviceAttributes as A1Attributes
from .taichuan.devices.ac.device import DeviceAttributes as ACAttributes
from .taichuan.devices.b0.device import DeviceAttributes as B0Attributes
from .taichuan.devices.b1.device import DeviceAttributes as B1Attributes
from .taichuan.devices.b3.device import DeviceAttributes as B3Attributes
from .taichuan.devices.b4.device import DeviceAttributes as B4Attributes
from .taichuan.devices.b6.device import DeviceAttributes as B6Attributes
from .taichuan.devices.bf.device import DeviceAttributes as BFAttributes
from .taichuan.devices.c2.device import DeviceAttributes as C2Attributes
from .taichuan.devices.c3.device import DeviceAttributes as C3Attributes
from .taichuan.devices.ca.device import DeviceAttributes as CAAttributes
from .taichuan.devices.cc.device import DeviceAttributes as CCAttributes
from .taichuan.devices.cd.device import DeviceAttributes as CDAttributes
from .taichuan.devices.ce.device import DeviceAttributes as CEAttributes
from .taichuan.devices.cf.device import DeviceAttributes as CFAttributes
from .taichuan.devices.da.device import DeviceAttributes as DAAttributes
from .taichuan.devices.db.device import DeviceAttributes as DBAttributes
from .taichuan.devices.dc.device import DeviceAttributes as DCAttributes
from .taichuan.devices.e1.device import DeviceAttributes as E1Attributes
from .taichuan.devices.e2.device import DeviceAttributes as E2Attributes
from .taichuan.devices.e3.device import DeviceAttributes as E3Attributes
from .taichuan.devices.e6.device import DeviceAttributes as E6Attributes
from .taichuan.devices.e8.device import DeviceAttributes as E8Attributes
from .taichuan.devices.ea.device import DeviceAttributes as EAAttributes
from .taichuan.devices.ec.device import DeviceAttributes as ECAttributes
from .taichuan.devices.ed.device import DeviceAttributes as EDAttributes
from .taichuan.devices.fa.device import DeviceAttributes as FAAttributes
from .taichuan.devices.fb.device import DeviceAttributes as FBAttributes
from .taichuan.devices.fc.device import DeviceAttributes as FCAttributes
from .taichuan.devices.fd.device import DeviceAttributes as FDAttributes """


TAICHUAN_DEVICES = {
    0x06: {
        "name": "Main Light",
        "entities": {
            "light": {
                "type": Platform.LIGHT,
                "icon": "mdi:lightbulb",
                "roomId": None,
                "name": "Main Light",
                "ctrlId": None
            },
        }
    },
    0x0A:{
        "name": "curton",
        "entities": {
            "curton": {
                "type": Platform.BUTTON,
                "icon": "mdi:button",
                "roomId": None,
                "name": "Button",
                "ctrlId": None
            }
        }
    },
    0x14:{
        "name": "scene",
        "entities": {
            "curton": {
                "type": Platform.BUTTON,
                "icon": "mdi:button",
                "roomId": None,
                "name": "Button",
                "ctrlId": None
            }
        }
    }
}

from homeassistant.const import Platform
DOMAIN = "taichuan_light"
COMPONENT = "component"
DEVICES = "devices"
CONF_KEY = "key"
CONF_MODEL = "model"
CONF_DEVTYPE = "devType"
CONF_ACCOUNT = "account"
CONF_SERVER = "server"
CONF_REFRESH_INTERVAL = "refresh_interval"
EXTRA_SENSOR = [Platform.SENSOR, Platform.BINARY_SENSOR]
EXTRA_SWITCH = [Platform.SWITCH, Platform.LOCK, Platform.SELECT, Platform.NUMBER]
EXTRA_CONTROL = [Platform.CLIMATE, Platform.WATER_HEATER, Platform.FAN, Platform.HUMIDIFIER, Platform.LIGHT] + \
                EXTRA_SWITCH
EXTRA_LIGHT = [Platform.LIGHT]
ALL_PLATFORM = EXTRA_LIGHT

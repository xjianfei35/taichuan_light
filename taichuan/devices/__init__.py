from importlib import import_module
#from homeassistant.helpers.importlib import async_import_module
#from homeassistant.core import HomeAssistant.
def device_selector(
    name: str,
    device_id: int,
    device_type: int,
):
    try:
        if device_type < 0xA0:
            device_path = f".{'x%02x' % device_type}.device"
        else:
            device_path = f".{'%02x' % device_type}.device"
        module = import_module(device_path, __package__)
        device = module.TaichuanAppliance(
            name=name,
            device_id=device_id,
            device_type=device_type,
        )
    except ModuleNotFoundError:
        device = None
    return device

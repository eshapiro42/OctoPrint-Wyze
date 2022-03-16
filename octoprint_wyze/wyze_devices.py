from wyze_sdk import Client
from wyze_sdk.errors import WyzeClientConfigurationError


class Wyze:
    def __init__(self, email, password):
        try:
            self.client = Client(email=email, password=password)
        except WyzeClientConfigurationError:
            self.client = None
        self.refresh_devices()

    def refresh_devices(self):
        self.devices = {}
        if self.client is None:
            return
        for device in self.client.devices_list():
            wyze_device = WyzeDeviceFactory(self.client, device)
            self.devices[device.mac] = wyze_device

    def get_device_by_mac(self, device_mac):
        return self.devices[device_mac]


class WyzeDevice:
    def __init__(self, device):
        self.device = device
        self.name = device.nickname
        self.type = device.type
        self.mac = device.mac
        self.model = device.product.model

    def turn_on(self):
        self.client.turn_on(
            device_mac=self.mac,
            device_model=self.model
        )

    def turn_off(self):
        self.client.turn_off(
            device_mac=self.mac,
            device_model=self.model
        )

    @property
    def is_online(self):
        return self.device.is_online

    @property
    def is_on(self):
        if self.device.is_on:
            return "On"
        return "Off"

    def __str__(self):
        return self.name


class WyzeLight(WyzeDevice):
    def __init__(self, client, device):
        self.client = client.lights
        return super().__init__(device)


class WyzePlug(WyzeDevice):
    def __init__(self, client, device):
        self.client = client.plugs
        return super().__init__(device)


class WyzeCamera(WyzeDevice):
    def __init__(self, client, device):
        self.client = client.cameras
        return super().__init__(device)


WYZE_DEVICE_TYPES = {
    "Light": WyzeLight,
    "Plug": WyzePlug,
    "Camera": WyzeCamera,
}


def WyzeDeviceFactory(client, device):
    return WYZE_DEVICE_TYPES[device.type](client, device)







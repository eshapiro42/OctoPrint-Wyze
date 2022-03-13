from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError


class WyzeDevices:
    def __init__(self, email, password):
        self.client = Client(email=email, password=password)
        self.refresh_devices()

    def refresh_devices(self):
        self.devices = {
            "Light": [],
            "Plug": [],
            "Camera": [],
        }
        for device in self.client.devices_list():
            self.devices[device.type].append(WyzeDevice(device))


class WyzeDevice:
    def __init__(self, device):
        self.device = device
        self.name = device.nickname
        self.type = device.type
        self.mac = device.mac

    @property
    def is_online(self):
        return self.device.is_online

    @property
    def is_on(self):
        if self.device.is_on:
            return "on"
        return "off"

    def __str__(self):
        return self.name
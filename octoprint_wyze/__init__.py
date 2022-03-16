# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from octoprint.plugin import (
    AssetPlugin,
    EventHandlerPlugin,
    SettingsPlugin,
    SimpleApiPlugin,
    StartupPlugin,
    TemplatePlugin, 
)

from .events import Event, Action, EventHandler
from .wyze_devices import Wyze, WYZE_DEVICE_TYPES


class WyzePlugin(
    AssetPlugin,
    EventHandlerPlugin,
    SettingsPlugin,
    SimpleApiPlugin,
    StartupPlugin,
    TemplatePlugin,
):
    def on_startup(self, host, port):
        try:
            self.wyze = Wyze(
                email=self._settings.get(["wyze_email"]),
                password=self._settings.get(["wyze_password"])
            )
            self.event_handler = None
            self._logger.info("Wyze Plugin successfully connected to Wyze!")
        except:
            self._logger.info("Wyze Plugin could not connect to Wyze.")
            raise


    def on_after_startup(self):
        self.data_folder = self.get_plugin_data_folder()
        self.event_handler = EventHandler(self.data_folder, self._logger)


    def get_settings_defaults(self):
        return dict(
            wyze_email=None,
            wyze_password=None,
        )

    
    def get_template_vars(self):
        return dict(
            email=self._settings.get(["wyze_email"]),
            device_types=WYZE_DEVICE_TYPES,
            devices=self.wyze.devices,
        )


    def get_template_configs(self):
        return [
            dict(
                type="settings",
                custom_bindings=False,
            ),
        ]


    def get_assets(self):
        return dict(
            css=["css/wyze.css"],
            js=["js/wyze.js"],
        )


    def get_api_commands(self):
        return dict(
            turn_on=["device_mac"],
            turn_off=["device_mac"],
        )


    def on_api_command(self, command, data):
        if command == "turn_on":
            device_mac = data["device_mac"]
            device = self.wyze.devices[device_mac]
            self._logger.info(f"Turning on Wyze {device.type} with device_mac={device_mac}...")
            device.turn_on()
        elif command == "turn_off":
            device_mac = data["device_mac"]
            device = self.wyze.devices[device_mac]
            self._logger.info(f"Turning off Wyze {device.type} with device_mac={device_mac}...")
            device.turn_off()

    
    def on_event(self, event_name, payload):
        if not hasattr(self, "event_handler") or Event.get_by_name(event_name) is None:
            return
        for device_mac in self.wyze.devices:
            if (action := self.event_handler.get_action(device_mac, event_name)) is None:
                continue
            self._logger.info(f"Calling device_mac={device_mac} event={event_name} action={action}")
            device = self.wyze.get_device_by_mac(device_mac)
            if action == Action.TURN_ON:
                device.turn_on()
            elif action == Action.TURN_OFF:
                device.turn_off()           
        

__plugin_pythoncompat__ = ">=3.8,<4"
__plugin_implementation__ = WyzePlugin()

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import flask
from octoprint.plugin import (
    AssetPlugin,
    EventHandlerPlugin,
    SettingsPlugin,
    SimpleApiPlugin,
    StartupPlugin,
    TemplatePlugin, 
)

from .events import Event, Action, EventHandler
from .wyze_devices import Wyze


class WyzePlugin(
    AssetPlugin,
    EventHandlerPlugin,
    SettingsPlugin,
    SimpleApiPlugin,
    StartupPlugin,
    TemplatePlugin,
):
    def on_startup(self, host, port):
        self.wyze = Wyze(
            email=self._settings.get(["wyze_email"]),
            password=self._settings.get(["wyze_password"])
        )


    def on_after_startup(self):
        self.data_folder = self.get_plugin_data_folder()
        self.event_handler = EventHandler(self.data_folder)


    def get_settings_defaults(self):
        return dict(
            wyze_email=None,
            wyze_password=None,
        )

    
    def get_template_vars(self):
        return dict(
            email=self._settings.get(["wyze_email"]),
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
            get_enums=[],
            get_devices=[],
            turn_on=["device_mac"],
            turn_off=["device_mac"],
            register=["device_mac", "event_name", "action_name"],
            unregister=["device_mac", "event_name", "action_name"],
        )


    def on_api_command(self, command, data):
        if command == "get_enums":
            self._logger.info("Sending enums...")
            enums = {
                "events": [Event.get_name(event) for event in Event],
                "actions": [Action.get_name(action) for action in Action],
            }
            return flask.jsonify(enums)
        elif command == "get_devices":
            self._logger.info("Sending device info...")
            devices = self.wyze.get_devices(self.event_handler)
            return flask.jsonify(devices)
        elif command == "turn_on":
            device_mac = data["device_mac"]
            device = self.wyze.devices[device_mac]
            self._logger.info(f"Turning on Wyze {device.type} with device_mac={device_mac}...")
            device.turn_on()
        elif command == "turn_off":
            device_mac = data["device_mac"]
            device = self.wyze.devices[device_mac]
            self._logger.info(f"Turning off Wyze {device.type} with device_mac={device_mac}...")
            device.turn_off()
        elif command == "register":
            device_mac = data["device_mac"]
            event_name = data["event_name"]
            event = Event.get_by_name(event_name)
            action_name = data["action_name"]
            action = Action.get_by_name(action_name)
            self._logger.info(f"Registering device_mac={device_mac} event={event} action={action}.")
            self.event_handler.register(device_mac, event, action)
        elif command == "unregister":
            device_mac = data["device_mac"]
            event_name = data["event_name"]
            event = Event.get_by_name(event_name)
            action_name = data["action_name"]
            action = Action.get_by_name(action_name)
            self._logger.info(f"Unregistering device_mac={device_mac} event={event} action={action}.")
            self.event_handler.unregister(device_mac, event, action)

    
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

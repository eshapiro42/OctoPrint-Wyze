# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import flask
from cryptography.fernet import Fernet
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
    def on_after_startup(self):
        self.data_folder = self.get_plugin_data_folder()
        self.event_handler = EventHandler(self.data_folder)


    def get_settings_defaults(self):
        return dict(
            wyze_email=None,
            wyze_password=None,
            wyze_key=None,
        )


    def on_settings_save(self, data):
        if "wyze_password" in data:
            # Encrypt the password
            password = data["wyze_password"]
            key = Fernet.generate_key()
            fernet = Fernet(key)
            encrypted_password = fernet.encrypt(password.encode())
            data["wyze_password"] = encrypted_password
            data["wyze_key"] = key
            # Try to connect to Wyze
            self.wyze = Wyze(
                email=self._settings.get(["wyze_email"]),
                password=password
            )
        SettingsPlugin.on_settings_save(self, data)


    def on_settings_load(self):
        data = SettingsPlugin.on_settings_load(self)
        if data["wyze_password"] is not None:
            # Decrypt the password
            encrypted_password = data["wyze_password"]
            key = data["wyze_key"]
            fernet = Fernet(key)
            password = fernet.decrypt(encrypted_password).decode()
            data["wyze_password"] = password
            # Try to connect to Wyze
            self.wyze = Wyze(
                email=self._settings.get(["wyze_email"]),
                password=password
            )
        return data

    
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
        if not hasattr(self, "wyze") or not hasattr(self, "event_handler") or Event.get_by_name(event_name) is None:
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


    def get_update_information(self):
        return dict(
            wyze=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,
                type="github_release",
                current=self._plugin_version,
                user="eshapiro42",
                repo="OctoPrint-Wyze",
                pip="https://github.com/eshapiro42/OctoPrint-Wyze/archive/refs/tag/v{target_version}.zip"
            )
        )   
        

__plugin_pythoncompat__ = ">=3.8,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = WyzePlugin()
    
    global __plugin_hooks__ 
    __plugin_hooks = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    }

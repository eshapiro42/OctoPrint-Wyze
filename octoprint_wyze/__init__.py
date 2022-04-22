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
from .events import (
    ActionType,
    EventHandler,
    EventType,
)
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
        self.pending_actions = []


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
            get_pending_actions=[],
            turn_on=["device_mac"],
            turn_off=["device_mac"],
            register=["device_mac", "event_name", "action_name"],
            unregister=["device_mac", "event_name", "action_name"],
            add_cancel=["device_mac", "event_name", "action_name"],
            remove_cancel=["device_mac", "event_name", "action_name"],
        )


    def on_api_command(self, command, data):
        if command == "get_enums":
            self._logger.info("Sending enums...")
            enums = {
                "events": [EventType.get_name(event) for event in EventType],
                "actions": [ActionType.get_name(action) for action in ActionType],
            }
            return flask.jsonify(enums)
        elif command == "get_devices":
            self._logger.info("Sending device info...")
            devices = self.wyze.get_devices(self.event_handler)
            return flask.jsonify(devices)
        elif command == "get_pending_actions":
            pending_actions = [str(action) for action in self.pending_actions]
            return flask.jsonify(pending_actions)
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
            event_type = EventType.get_by_name(event_name)
            action_name = data["action_name"]
            action_type = ActionType.get_by_name(action_name)
            delay = data["delay"]
            self._logger.info(f"Registering device_mac={device_mac} event={event_type} action={action_type} delay={delay}.")
            self.event_handler.register(device_mac, event_type, action_type, delay)
        elif command == "unregister":
            device_mac = data["device_mac"]
            event_name = data["event_name"]
            event_type = EventType.get_by_name(event_name)
            action_name = data["action_name"]
            action_type = ActionType.get_by_name(action_name)
            self._logger.info(f"Unregistering device_mac={device_mac} event={event_type} action={action_type}.")
            self.event_handler.unregister(device_mac, event_type, action_type)
            # Cancel any pending actions that match
            matched_actions = []
            for action in self.pending_actions:
                if action.device.mac == device_mac and action.event_type == event_type and action.action_type == action_type:
                    matched_actions.append(action)
            for action in matched_actions:
                self._logger.info(f"Cancelling pending action {action}...")
                action.cancel()
        elif command == "add_cancel":
            device_mac = data["device_mac"]
            event_name = data["event_name"]
            event_type = EventType.get_by_name(event_name)
            action_name = data["action_name"]
            action_type = ActionType.get_by_name(action_name)
            self._logger.info(f"Adding cancellation device_mac={device_mac} event={event_type} action={action_type}.")
            self.event_handler.add_cancel(device_mac, event_type, action_type)
        elif command == "remove_cancel":
            device_mac = data["device_mac"]
            event_name = data["event_name"]
            event_type = EventType.get_by_name(event_name)
            action_name = data["action_name"]
            action_type = ActionType.get_by_name(action_name)
            self._logger.info(f"Removing cancellation device_mac={device_mac} event={event_type} action={action_type}.")
            self.event_handler.remove_cancel(device_mac, event_type, action_type)

    
    def on_event(self, event_name, payload):
        if not hasattr(self, "wyze") or not hasattr(self, "event_handler") or EventType.get_by_name(event_name) is None:
            return
        for device_mac in self.wyze.devices:
            device = self.wyze.get_device_by_mac(device_mac)
            # Cancel any pending actions that are supposed to be cancelled on this event
            self.event_handler.process_cancellations(self, device, event_name)
            # Add event handlers for any registerations that match this event
            if (action := self.event_handler.get_action(self, device, event_name)) is None:
                continue
            if any(action.device == device for action in self.pending_actions):
                continue
            self.pending_actions.append(action)
            action.start()


    def get_update_information(self):
        return dict(
            wyze=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,
                type="github_release",
                current=self._plugin_version,
                user="eshapiro42",
                repo="OctoPrint-Wyze",
                pip="https://github.com/eshapiro42/OctoPrint-Wyze/archive/{target_version}.zip"
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

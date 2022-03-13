# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from octoprint.plugin import (
    AssetPlugin,
    SettingsPlugin,
    StartupPlugin,
    TemplatePlugin, 
)

from .wyze_devices import WyzeDevices


class WyzePlugin(
    AssetPlugin,
    SettingsPlugin,
    StartupPlugin,
    TemplatePlugin,
):

    def on_after_startup(self):
        try:
            self.wyze_devices = WyzeDevices(
                email=self._settings.get(["wyze_email"]),
                password=self._settings.get(["wyze_password"])
            )
            print("Wyze Plugin successfully connected to Wyze!")
        except:
            print("Wyze Plugin could not connect to Wyze.")


    def get_settings_defaults(self):
        return dict(
            wyze_email=None,
            wyze_password=None,
        )

    
    def get_template_vars(self):
        return dict(
            email=self._settings.get(["wyze_email"]),
            devices=self.wyze_devices.devices,
        )


    def get_template_configs(self):
        return [
            dict(
                type="settings",
                custom_bindings=False,
            ),
            dict(
                type="tab",
                custom_bindings=False,
            )
        ]

    def get_assets(self):
        return dict(
            css=["css/wyze.css"],
        )


__plugin_pythoncompat__ = ">=3.8,<4"
__plugin_implementation__ = WyzePlugin()

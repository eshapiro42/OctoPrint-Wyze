/*
 * View model for OctoPrint-Wyze
 *
 * Author: Eric Shapiro
 * License: AGPLv3
 */
$(function() {
    function WyzeViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];

        self.turnOnDevice = function(device_mac) {
            OctoPrint.simpleApiCommand(
                "wyze",
                "turn_on", 
                {
                    "device_mac": device_mac,
                }
            );
        };

        self.turnOffDevice = function(device_mac) {
            OctoPrint.simpleApiCommand(
                "wyze",
                "turn_off", 
                {
                    "device_mac": device_mac,
                }
            );
        };

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: WyzeViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_wyze, #tab_plugin_wyze, ...
        elements: ["#tab_plugin_wyze"]
    });
});

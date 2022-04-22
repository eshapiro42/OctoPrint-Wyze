/*
 * View model for OctoPrint-Wyze
 *
 * Author: Eric Shapiro
 * License: AGPLv3
 */

$(function() {
    function WyzeViewModel(parameters, js_event) {
        var self = this;

        self.actions = [];
        self.events = [];
        self.pendingActions = ko.observableArray([]);
        self.devices = ko.observableArray([]);

        OctoPrint.simpleApiCommand(
            "wyze",
            "get_enums",
        ).done(function(response) {
            self.events = response.events;
            self.actions = response.actions;
        });

        function getPendingActions() {
            OctoPrint.simpleApiCommand(
                "wyze",
                "get_pending_actions",
            ).done(function(response) {
                self.pendingActions(response);
            });
        }

        var getPendingActionsInterval = window.setInterval(getPendingActions, 500);

        function Device(data) {
            var this_device = this;

            this_device.mac = data.device_mac;
            this_device.name = data.device_name;
            this_device.type = data.device_type;

            this_device.turnOnDevice = function() {
                OctoPrint.simpleApiCommand(
                    "wyze",
                    "turn_on", 
                    {
                        "device_mac": this_device.mac,
                    }
                );
            };
    
            this_device.turnOffDevice = function() {
                OctoPrint.simpleApiCommand(
                    "wyze",
                    "turn_off", 
                    {
                        "device_mac": this_device.mac,
                    }
                );
            };

            this_device.registerDevice = function(event_index, action_name, delay) {
                event_name = self.events[event_index];
                OctoPrint.simpleApiCommand(
                    "wyze",
                    "register",
                    {
                        "device_mac": this_device.mac,
                        "event_name": event_name,
                        "action_name": action_name,
                        "delay": delay,
                    }
                )
            }

            this_device.unregisterDevice = function(event_index, action_name) {
                event_name = self.events[event_index];
                OctoPrint.simpleApiCommand(
                    "wyze",
                    "unregister",
                    {
                        "device_mac": this_device.mac,
                        "event_name": event_name,
                        "action_name": action_name,
                    }
                )
            }

            this_device.addCancel = function(event_index, action_name) {
                event_name = self.events[event_index];
                OctoPrint.simpleApiCommand(
                    "wyze",
                    "add_cancel",
                    {
                        "device_mac": this_device.mac,
                        "event_name": event_name,
                        "action_name": action_name,
                    }
                )
            }

            this_device.removeCancel = function(event_index, action_name) {
                event_name = self.events[event_index];
                OctoPrint.simpleApiCommand(
                    "wyze",
                    "remove_cancel",
                    {
                        "device_mac": this_device.mac,
                        "event_name": event_name,
                        "action_name": action_name,
                    }
                )
            }

            this_device.turnOnCancelClicked = function(data, js_event) {
                var context = ko.contextFor(js_event.target);
                var event_index = context.$index();
                this_device.turn_on_registrations[event_index].cancel(!this_device.turn_on_registrations[event_index].cancel());
                var checked = this_device.turn_on_registrations[event_index].cancel();
                if (checked) {
                    this_device.addCancel(event_index, "TurnOn");
                }
                else {
                    this_device.removeCancel(event_index, "TurnOn");
                }
                return true;
            }
            
            this_device.turnOffCancelClicked = function(data, js_event) {
                var context = ko.contextFor(js_event.target);
                var event_index = context.$index();
                this_device.turn_off_registrations[event_index].cancel(!this_device.turn_off_registrations[event_index].cancel());
                var checked = this_device.turn_off_registrations[event_index].cancel();
                if (checked) {
                    this_device.addCancel(event_index, "TurnOff");
                }
                else {
                    this_device.removeCancel(event_index, "TurnOff");
                }
                return true;
            }

            this_device.turnOnCheckBoxClicked = function(data, js_event) {
                var context = ko.contextFor(js_event.target);
                var event_index = context.$index();
                var checked = js_event.currentTarget.checked;
                if (checked) {
                    var delay = js_event.currentTarget.nextElementSibling.valueAsNumber;
                    this_device.registerDevice(event_index, "TurnOn", delay);
                }
                else {
                    this_device.unregisterDevice(event_index, "TurnOn");
                }
                return true;
            }

            this_device.turnOffCheckBoxClicked = function(data, js_event) {
                var context = ko.contextFor(js_event.target);
                var event_index = context.$index();
                var checked = js_event.currentTarget.checked;
                if (checked) {
                    var delay = js_event.currentTarget.nextElementSibling.valueAsNumber;
                    this_device.registerDevice(event_index, "TurnOff", delay);
                }
                else {
                    this_device.unregisterDevice(event_index, "TurnOff");
                }
                return true;
            }

            this_device.turn_on_registrations = $.map(data.turn_on_registrations, function(item, event_index) {
                var registration = {
                    eventIndex: event_index,
                    registered: ko.observable(item.registered),
                    delay: ko.observable(item.delay),
                    cancel: ko.observable(item.cancel),
                };
                return registration;
            });

            this_device.turn_off_registrations = $.map(data.turn_off_registrations, function(item, event_index) {
                var registration = {
                    eventIndex: event_index,
                    registered: ko.observable(item.registered),
                    delay: ko.observable(item.delay),
                    cancel: ko.observable(item.cancel),
                };
                return registration;
            });
        }

        OctoPrint.simpleApiCommand(
            "wyze",
            "get_devices",
        ).done(function(response) {
            var devices = $.map(response, function(item) {
                return new Device(item);
            });
            self.devices(devices);
        });

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
        dependencies: [],
        // Elements to bind to, e.g. #settings_plugin_wyze, #tab_plugin_wyze, ...
        elements: ["#tab_plugin_wyze"]
    });
});

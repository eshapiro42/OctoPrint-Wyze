from __future__ import annotations
from collections import defaultdict

import os
import sqlite3
import time

from contextlib import contextmanager
from enum import IntEnum, auto
from threading import Thread
from typing import Optional, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .wyze_devices import WyzeDevice


class EventType(IntEnum):
    CLIENT_OPENED = 0
    CLIENT_CLOSED = auto()
    PRINT_STARTED = auto()
    PRINT_FAILED = auto()
    PRINT_DONE = auto()
    PRINT_CANCELLED = auto()
    PRINT_PAUSED = auto()
    PRINT_RESUMED = auto()
    CAPTURE_START = auto()
    CAPTURE_DONE = auto()
    CAPTURE_FAILED = auto()


    @classmethod
    def names(cls):
        return {
            cls.CLIENT_OPENED: "ClientOpened",
            cls.CLIENT_CLOSED: "ClientClosed",
            cls.PRINT_STARTED: "PrintStarted",
            cls.PRINT_FAILED: "PrintFailed",
            cls.PRINT_DONE: "PrintDone",
            cls.PRINT_CANCELLED: "PrintCancelled",
            cls.PRINT_PAUSED: "PrintPaused",
            cls.PRINT_RESUMED: "PrintResumed",
            cls.CAPTURE_START: "CaptureStart",
            cls.CAPTURE_DONE: "CaptureDone",
            cls.CAPTURE_FAILED: "CaptureFailed",
        }


    @classmethod
    def get_by_name(cls, event_name: str) -> Optional[EventType]:
        reversed_names = {v: k for k, v in cls.names().items()}
        try:
            return reversed_names[event_name]
        except KeyError:
            return None


    @classmethod
    def get_name(cls, event: EventType) -> Optional[str]:
        try:
            return cls.names()[event]
        except KeyError:
            return None


class ActionType(IntEnum):
    TURN_ON = 0
    TURN_OFF = auto()


    @classmethod
    def names(cls):
        return {
            cls.TURN_ON: "TurnOn",
            cls.TURN_OFF: "TurnOff",
        }


    @classmethod
    def get_by_name(cls, action_name: str) -> Optional[ActionType]:
        reversed_names = {v: k for k, v in cls.names().items()}
        try:
            return reversed_names[action_name]
        except KeyError:
            return None


    @classmethod
    def get_name(cls, action: ActionType) -> Optional[str]:
        try:
            return cls.names()[action]
        except KeyError:
            return None


class Action(Thread):
    def __init__(self, plugin, action_type: ActionType, event_type: EventType, device: WyzeDevice, delay: float = 0):
        super().__init__(daemon=True)
        self.action_type = action_type
        self.action_name = "turn on" if action_type == ActionType.TURN_ON else "turn off"
        self.event_type = event_type
        self.device = device
        self.plugin = plugin
        self.delay = delay
        self.device = device
        self.delay = delay * 60 # Convert minutes to seconds
        self.time_remaining = self.delay
        self.plugin = plugin
        self._cancel = False


    def run(self):
        start = time.time()
        while time.time() - start < self.delay:
            if self._cancel:
                break
            self.time_remaining = self.delay - (time.time() - start)
            time.sleep(0.5)
        if not self._cancel:
            if self.action_type == ActionType.TURN_ON:
                self.device.turn_on()
            elif self.action_type == ActionType.TURN_OFF:
                self.device.turn_off()
            self.plugin.pending_actions.remove(self)


    def cancel(self):
        self._cancel = True
        self.plugin.pending_actions.remove(self)


    def __str__(self):
        return f"{EventType.get_name(self.event_type)}: {self.device} will {self.action_name} in {round(self.time_remaining)} seconds."


class EventHandler:
    def __init__(self, data_folder: str):
        self.db_path = os.path.join(data_folder, "wyze-event-handler-v2.db")
        self.create_tables()

    
    @contextmanager
    def db_conn(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        yield cur
        conn.commit()
        conn.close()


    def create_tables(self):
        with self.db_conn() as cur:
            cur.execute(
                """
                    CREATE TABLE IF NOT EXISTS
                        registrations
                        (
                            device_mac text,
                            event_name text,
                            action_name text,
                            delay real
                        )
                """
            )
            cur.execute(
                """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                        mac_event_action
                    ON
                        registrations
                    (
                        device_mac,
                        event_name,
                        action_name
                    )
                """
            )
            cur.execute(
                """
                    CREATE TABLE IF NOT EXISTS
                        cancellations
                        (
                            device_mac text,
                            event_name text,
                            action_name text
                        )
                """
            )
            cur.execute(
                """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                        mac_event_action
                    ON
                        cancellations
                    (
                        device_mac,
                        event_name,
                        action_name
                    )
                """
            )


    def register(self, device_mac: str, event: EventType, action: ActionType, delay: float = 0):
        with self.db_conn() as cur:
            try:
                cur.execute(
                    """
                        INSERT INTO
                            registrations
                        VALUES
                            (?, ?, ?, ?)
                    """,
                    (device_mac, EventType.get_name(event), ActionType.get_name(action), delay)
                )
            except sqlite3.IntegrityError:
                pass


    def unregister(self, device_mac: str, event: EventType, action: ActionType):
        with self.db_conn() as cur:
            cur.execute(
                """
                    DELETE FROM
                        registrations
                    WHERE
                        device_mac = ?
                        AND
                        event_name = ?
                        AND 
                        action_name = ?
                """,
                (device_mac, EventType.get_name(event), ActionType.get_name(action))
            )


    def add_cancel(self, device_mac: str, event: EventType, action: ActionType):
        with self.db_conn() as cur:
            try:
                cur.execute(
                    """
                        INSERT INTO
                            cancellations
                        VALUES
                            (?, ?, ?)
                    """,
                    (device_mac, EventType.get_name(event), ActionType.get_name(action))
                )
            except sqlite3.IntegrityError:
                pass


    def remove_cancel(self, device_mac: str, event: EventType, action: ActionType):
        with self.db_conn() as cur:
            cur.execute(
                """
                    DELETE FROM
                        cancellations
                    WHERE
                        device_mac = ?
                        AND
                        event_name = ?
                        AND 
                        action_name = ?
                """,
                (device_mac, EventType.get_name(event), ActionType.get_name(action))
            )


    def get_action(self, plugin, device: WyzeDevice, event_name: str) -> Optional[ActionType]:
        with self.db_conn() as cur:
            cur.execute(
                """
                    SELECT * FROM
                        registrations
                    WHERE
                        device_mac = ?
                        AND
                        event_name = ?
                """,
                (device.mac, event_name)
            )
            result = cur.fetchone()
            if result is not None:
                action_name = result[2]
                delay = result[3]
                action_type = ActionType.get_by_name(action_name)
                event_type = EventType.get_by_name(event_name)
                return Action(plugin, action_type, event_type, device, delay)
            return None

        
    def process_cancellations(self, plugin, device: WyzeDevice, event_name: str):
        with self.db_conn() as cur:
            for _, event_name, action_name in cur.execute(
                """
                    SELECT * FROM
                        cancellations
                    WHERE
                        device_mac = ?
                        AND
                        event_name = ?
                """,
                (device.mac, event_name)
            ):
                action_type = ActionType.get_by_name(action_name)
                matched_actions = []
                for action in plugin.pending_actions:
                    if action.device.mac == device.mac and action.action_type == action_type:
                        matched_actions.append(action)
                for action in matched_actions:
                    plugin._logger.info(f"Event {event_name} fired. Cancelling pending action {action}...")
                    action.cancel()
            
    
    def get_registrations(self, device_mac: str) -> Tuple[List]:
        turn_on_registrations = []
        turn_off_registrations = []
        for _ in EventType:
            turn_on_registrations.append(
                {
                    "registered": False,
                    "delay": 0,
                    "cancel": False
                }
            )
            turn_off_registrations.append(
                {
                    "registered": False,
                    "delay": 0,
                    "cancel": False
                }
            )
        with self.db_conn() as cur:
            for _, event_name, action_name, delay in cur.execute(
                """
                    SELECT * FROM
                        registrations
                    WHERE
                        device_mac = ?
                """,
                (device_mac, )
            ):
                event_type = EventType.get_by_name(event_name)
                action_type = ActionType.get_by_name(action_name)
                if action_type == ActionType.TURN_ON:
                    turn_on_registrations[event_type]["registered"] = True
                    turn_on_registrations[event_type]["delay"] = delay
                elif action_type == ActionType.TURN_OFF:
                    turn_off_registrations[event_type]["registered"] = True
                    turn_off_registrations[event_type]["delay"] = delay
            for _, event_name, action_name in cur.execute(
                """
                    SELECT * FROM
                        cancellations
                    WHERE
                        device_mac = ?
                """,
                (device_mac, )
            ):
                event_type = EventType.get_by_name(event_name)
                action_type = ActionType.get_by_name(action_name)
                if action_type == ActionType.TURN_ON:
                    turn_on_registrations[event_type]["cancel"] = True
                elif action_type == ActionType.TURN_OFF:
                    turn_off_registrations[event_type]["cancel"] = True
        return turn_on_registrations, turn_off_registrations

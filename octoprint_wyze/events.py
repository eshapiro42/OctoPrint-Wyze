from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from enum import IntEnum, auto
from typing import Optional, List, Tuple


class Event(IntEnum):
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
    def get_by_name(cls, event_name: str) -> Optional[Event]:
        reversed_names = {v: k for k, v in cls.names().items()}
        try:
            return reversed_names[event_name]
        except KeyError:
            return None


    @classmethod
    def get_name(cls, event: Event) -> Optional[str]:
        try:
            return cls.names()[event]
        except KeyError:
            return None


class Action(IntEnum):
    TURN_ON = 0
    TURN_OFF = auto()


    @classmethod
    def names(cls):
        return {
            cls.TURN_ON: "TurnOn",
            cls.TURN_OFF: "TurnOff",
        }


    @classmethod
    def get_by_name(cls, action_name: str) -> Optional[Action]:
        reversed_names = {v: k for k, v in cls.names().items()}
        try:
            return reversed_names[action_name]
        except KeyError:
            return None


    @classmethod
    def get_name(cls, action: Action) -> Optional[str]:
        try:
            return cls.names()[action]
        except KeyError:
            return None


class EventHandler:
    def __init__(self, data_folder: str):
        self.db_path = os.path.join(data_folder, "wyze-event-handler.db")
        self.create_table()

    
    @contextmanager
    def db_conn(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        yield cur
        conn.commit()
        conn.close()


    def create_table(self):
        with self.db_conn() as cur:
            cur.execute(
                """
                    CREATE TABLE IF NOT EXISTS
                        registrations
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
                        registrations
                    (
                        device_mac,
                        event_name,
                        action_name
                    )
                """
            )


    def register(self, device_mac: str, event: Event, action: Action):
        with self.db_conn() as cur:
            try:
                cur.execute(
                    """
                        INSERT INTO
                            registrations
                        VALUES
                            (?, ?, ?)
                    """,
                    (device_mac, Event.get_name(event), Action.get_name(action))
                )
            except sqlite3.IntegrityError:
                pass


    def unregister(self, device_mac: str, event: Event, action: Action):
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
                (device_mac, Event.get_name(event), Action.get_name(action))
            )


    def get_action(self, device_mac: str, event_name: str) -> Optional[Action]:
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
                (device_mac, event_name)
            )
            result = cur.fetchone()
            if result is not None:
                action_name = result[2]
                return Action.get_by_name(action_name)
            return None

    
    def get_registrations(self, device_mac: str) -> Tuple[List]:
        turn_on_registrations = [False] * len(Event)
        turn_off_registrations = [False] * len(Event)
        with self.db_conn() as cur:
            for _, event_name, action_name in cur.execute(
                """
                    SELECT * FROM
                        registrations
                    WHERE
                        device_mac = ?
                """,
                (device_mac, )
            ):
                event = Event.get_by_name(event_name)
                action = Action.get_by_name(action_name)
                if action == Action.TURN_ON:
                    turn_on_registrations[event] = True
                elif action == Action.TURN_OFF:
                    turn_off_registrations[event] = True
        return turn_on_registrations, turn_off_registrations

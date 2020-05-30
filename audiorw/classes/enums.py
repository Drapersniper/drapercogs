# -*- coding: utf-8 -*-
# Standard Library
import enum

__all__ = {"PlayerStatus"}


class PlayerStatus(enum.Enum):
    READY = "Ready"
    DISCONNECTED = "Disconnected"
    PLAYING = "Playing"
    CONNECTED = "Connected"
    PAUSED = "Paused"

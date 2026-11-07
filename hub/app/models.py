"""Pydantic models and clamping rules for SunDial.

Limits (single source of truth, used by the hub, the tests, and mirrored
in firmware/micropython/dial.py):
  brightness 0-100 %, fan speed 0-3, HVAC target 16-30 C.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MIN_TEMP_C = 16.0
MAX_TEMP_C = 30.0
MAX_FAN_SPEED = 3


def clamp_brightness(value: int) -> int:
    return max(0, min(100, int(value)))


def clamp_fan_speed(value: int) -> int:
    return max(0, min(MAX_FAN_SPEED, int(value)))


def clamp_temp_c(value: float) -> float:
    return max(MIN_TEMP_C, min(MAX_TEMP_C, float(value)))


class DialMode(str, Enum):
    LIGHTS = "lights"
    FAN = "fan"
    HVAC = "hvac"

    @classmethod
    def next(cls, mode: "DialMode") -> "DialMode":
        order = [cls.LIGHTS, cls.FAN, cls.HVAC]
        return order[(order.index(mode) + 1) % len(order)]


class LightsConfig(BaseModel):
    entity_id: str
    default_brightness: int = 65

    @field_validator("default_brightness")
    @classmethod
    def _brightness(cls, v: int) -> int:
        return clamp_brightness(v)


class FanConfig(BaseModel):
    entity_id: str
    max_speed: int = 3

    @field_validator("max_speed")
    @classmethod
    def _speed(cls, v: int) -> int:
        return clamp_fan_speed(v)


class HvacConfig(BaseModel):
    entity_id: str
    default_target_temp_c: float = 21.5

    @field_validator("default_target_temp_c")
    @classmethod
    def _temp(cls, v: float) -> float:
        return clamp_temp_c(v)


class RoomConfig(BaseModel):
    id: str
    name: str
    dial_id: str
    poe_switch_port: int | None = None
    lights: LightsConfig
    fan: FanConfig
    hvac: HvacConfig


class RoomState(BaseModel):
    room_id: str
    lights_on: bool = False
    brightness: int = 65
    fan_on: bool = False
    fan_speed: int = 0
    hvac_mode: Literal["heat", "cool", "auto", "off"] = "auto"
    target_temp_c: float = 21.5
    current_temp_c: float = 21.0
    mode: DialMode = DialMode.LIGHTS

    @field_validator("brightness")
    @classmethod
    def _brightness(cls, v: int) -> int:
        return clamp_brightness(v)

    @field_validator("fan_speed")
    @classmethod
    def _speed(cls, v: int) -> int:
        return clamp_fan_speed(v)

    @field_validator("target_temp_c", "current_temp_c")
    @classmethod
    def _temp(cls, v: float) -> float:
        return clamp_temp_c(v)

    def centre_percent(self) -> int:
        """Value shown in the centre of the round dial for the active mode."""
        if self.mode == DialMode.LIGHTS:
            return self.brightness
        if self.mode == DialMode.FAN:
            return int(round(self.fan_speed / MAX_FAN_SPEED * 100)) if self.fan_on else 0
        # HVAC: map 16-30 C onto 0-100 for the ring.
        return int(round((self.target_temp_c - MIN_TEMP_C) / (MAX_TEMP_C - MIN_TEMP_C) * 100))


class LightsRequest(BaseModel):
    on: bool | None = None
    brightness: int | None = None

    @field_validator("brightness")
    @classmethod
    def _brightness(cls, v: int | None) -> int | None:
        return None if v is None else clamp_brightness(v)


class FanRequest(BaseModel):
    on: bool | None = None
    speed: int | None = None

    @field_validator("speed")
    @classmethod
    def _speed(cls, v: int | None) -> int | None:
        return None if v is None else clamp_fan_speed(v)


class HvacRequest(BaseModel):
    mode: Literal["heat", "cool", "auto", "off"] | None = None
    target_temp_c: float | None = None

    @field_validator("target_temp_c")
    @classmethod
    def _temp(cls, v: float | None) -> float | None:
        return None if v is None else clamp_temp_c(v)


class DialEvent(BaseModel):
    """One physical interaction from a wall dial."""
    mode: DialMode | None = None
    delta: int = 0
    action: Literal["rotate", "press", "tap", "long_press"] = "rotate"

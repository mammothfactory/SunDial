"""In-memory room state + dial-event handling (demo backend).

This is the single source of truth for state when HASS_DEMO=true (the
default). When a real Home Assistant is configured, the hub still keeps
this mirror so the dial, the companion app and the WebSocket all stay in
sync even if HA is briefly unreachable.
"""
from __future__ import annotations

from .models import DialEvent, DialMode, RoomConfig, RoomState, clamp_fan_speed, clamp_temp_c


class RoomStore:
    def __init__(self, configs: list[RoomConfig]) -> None:
        self.configs = {c.id: c for c in configs}
        self.states: dict[str, RoomState] = {
            c.id: RoomState(
                room_id=c.id,
                brightness=c.lights.default_brightness,
                fan_speed=0,
                target_temp_c=c.hvac.default_target_temp_c,
                current_temp_c=c.hvac.default_target_temp_c,
            )
            for c in configs
        }

    def get(self, room_id: str) -> RoomState:
        if room_id not in self.states:
            raise KeyError(room_id)
        return self.states[room_id]

    def set_lights(self, room_id: str, on: bool | None, brightness: int | None) -> RoomState:
        s = self.get(room_id)
        if on is not None:
            s.lights_on = on
        if brightness is not None:
            s.brightness = brightness
            s.lights_on = brightness > 0
        return s

    def set_fan(self, room_id: str, on: bool | None, speed: int | None) -> RoomState:
        s = self.get(room_id)
        if speed is not None:
            s.fan_speed = speed
            s.fan_on = speed > 0
        if on is not None:
            s.fan_on = on
            if not on:
                s.fan_speed = 0
            elif s.fan_speed == 0:
                s.fan_speed = 1
        return s

    def set_hvac(self, room_id: str, mode: str | None, target_temp_c: float | None) -> RoomState:
        s = self.get(room_id)
        if mode is not None:
            s.hvac_mode = mode  # type: ignore[assignment]
        if target_temp_c is not None:
            s.target_temp_c = target_temp_c
        return s

    def apply_dial_event(self, room_id: str, event: DialEvent) -> RoomState:
        """Rotate = adjust current mode; press = next mode; tap = toggle;
        long-press = everything in the room off."""
        s = self.get(room_id)
        # Dial events carry the dial's mode AFTER the local state machine
        # ran (firmware/micropython/dial.py returns post-action mode), so a
        # "press" must NOT advance again — it already advanced on the dial.
        if event.action == "press":
            s.mode = event.mode if event.mode is not None else DialMode.next(s.mode)
            return s
        if event.mode is not None:
            s.mode = event.mode
        if event.action == "long_press":
            s.lights_on, s.brightness = False, s.brightness
            s.fan_on, s.fan_speed = False, 0
            s.hvac_mode = "off"
            return s
        if event.action == "tap":
            if s.mode == DialMode.LIGHTS:
                s.lights_on = not s.lights_on
            elif s.mode == DialMode.FAN:
                s.fan_on = not s.fan_on
                s.fan_speed = 1 if s.fan_on and s.fan_speed == 0 else (0 if not s.fan_on else s.fan_speed)
            else:
                s.hvac_mode = "off" if s.hvac_mode != "off" else "auto"
            return s
        # rotate
        if event.delta == 0:
            return s
        if s.mode == DialMode.LIGHTS:
            s.brightness = max(0, min(100, s.brightness + event.delta * 5))
            s.lights_on = s.brightness > 0
        elif s.mode == DialMode.FAN:
            s.fan_speed = clamp_fan_speed(s.fan_speed + event.delta)
            s.fan_on = s.fan_speed > 0
        else:
            s.target_temp_c = clamp_temp_c(s.target_temp_c + event.delta * 0.5)
            if s.hvac_mode == "off":
                s.hvac_mode = "auto"
        return s

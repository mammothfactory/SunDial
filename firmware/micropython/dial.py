"""SunDial dial state machine (MicroPython, CPython-compatible).

Runs on the M5Stack Dial v1.1: 1.28" round TFT 240x240, rotary encoder
on GPIO40/41, button GPIO42, buzzer GPIO3.

Interaction (same contract as the hub's POST /rooms/{id}/dial/event):
  rotate     -> adjust the current mode (Lights +/-5% per detent,
                Fan +/-1 speed, HVAC +/-0.5 C per detent)
  press      -> next mode: Lights -> Fan -> HVAC -> Lights
  tap        -> toggle the current mode on/off
  long-press -> everything in the room off

This file has no hardware imports, so the same logic is unit-tested on
CPython in tests/test_dial.py. Hardware wiring lives in main.py / ui.py.
"""
try:
    from micropython import const  # type: ignore[import]
except ImportError:  # CPython (tests)
    def const(x):  # type: ignore[no-redef]
        return x

MODES = ("lights", "fan", "hvac")
MIN_TEMP_C = 16.0
MAX_TEMP_C = 30.0
MAX_FAN_SPEED = 3


def clamp_brightness(v):
    return max(0, min(100, int(v)))


def clamp_fan_speed(v):
    return max(0, min(MAX_FAN_SPEED, int(v)))


def clamp_temp_c(v):
    return max(MIN_TEMP_C, min(MAX_TEMP_C, float(v)))


class DialState:
    """Local mirror of one room's state, kept in sync with the hub."""

    def __init__(self, brightness=65, fan_speed=0, target_temp_c=21.5):
        self.mode = "lights"
        self.lights_on = False
        self.brightness = clamp_brightness(brightness)
        self.fan_on = False
        self.fan_speed = clamp_fan_speed(fan_speed)
        self.hvac_mode = "auto"
        self.target_temp_c = clamp_temp_c(target_temp_c)

    def centre_percent(self):
        if self.mode == "lights":
            return self.brightness
        if self.mode == "fan":
            return int(round(self.fan_speed / MAX_FAN_SPEED * 100)) if self.fan_on else 0
        return int(round((self.target_temp_c - MIN_TEMP_C) / (MAX_TEMP_C - MIN_TEMP_C) * 100))

    def next_mode(self):
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
        return self.mode

    def apply(self, action, delta=0):
        """Apply one interaction. Returns (action, mode, delta) to send to the hub."""
        if action == "long_press":
            self.lights_on = False
            self.fan_on = False
            self.fan_speed = 0
            self.hvac_mode = "off"
        elif action == "press":
            self.next_mode()
        elif action == "tap":
            if self.mode == "lights":
                self.lights_on = not self.lights_on
            elif self.mode == "fan":
                self.fan_on = not self.fan_on
                self.fan_speed = 1 if self.fan_on and self.fan_speed == 0 else (0 if not self.fan_on else self.fan_speed)
            else:
                self.hvac_mode = "off" if self.hvac_mode != "off" else "auto"
        elif action == "rotate" and delta:
            if self.mode == "lights":
                self.brightness = clamp_brightness(self.brightness + delta * 5)
                self.lights_on = self.brightness > 0
            elif self.mode == "fan":
                self.fan_speed = clamp_fan_speed(self.fan_speed + delta)
                self.fan_on = self.fan_speed > 0
            else:
                self.target_temp_c = clamp_temp_c(self.target_temp_c + delta * 0.5)
                if self.hvac_mode == "off":
                    self.hvac_mode = "auto"
        return {"mode": self.mode, "delta": delta, "action": action}

    def as_dict(self):
        return {
            "mode": self.mode,
            "lights_on": self.lights_on,
            "brightness": self.brightness,
            "fan_on": self.fan_on,
            "fan_speed": self.fan_speed,
            "hvac_mode": self.hvac_mode,
            "target_temp_c": self.target_temp_c,
            "centre_percent": self.centre_percent(),
        }

"""Tests for the dial state machine (firmware/micropython/dial.py) and the
hub's identical logic in hub/app/state.py — both must agree."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Load the MicroPython dial module by path (it is CPython-compatible).
_spec = importlib.util.spec_from_file_location(
    "fw_dial", ROOT / "firmware" / "micropython" / "dial.py")
fw_dial = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fw_dial)

from hub.app.models import DialEvent, DialMode  # noqa: E402
from hub.app.rooms import load_rooms  # noqa: E402
from hub.app.state import RoomStore  # noqa: E402


@pytest.fixture
def store():
    return RoomStore(load_rooms(ROOT / "config" / "rooms.yaml"))


def test_fw_rotate_lights_clamps_at_100():
    d = fw_dial.DialState(brightness=95)
    d.apply("rotate", 3)  # +15 -> clamped
    assert d.brightness == 100 and d.lights_on


def test_fw_rotate_fan_and_hvac():
    d = fw_dial.DialState()
    d.apply("press")  # -> fan
    d.apply("rotate", 5)
    assert d.fan_speed == 3 and d.fan_on
    d.apply("press")  # -> hvac
    d.apply("rotate", -20)
    assert d.target_temp_c == 16.0


def test_fw_press_cycles_modes():
    d = fw_dial.DialState()
    assert [d.apply("press")["mode"] for _ in range(3)] == ["fan", "hvac", "lights"]


def test_fw_tap_toggles_and_long_press_all_off():
    d = fw_dial.DialState()
    d.apply("tap")
    assert d.lights_on
    d.apply("long_press")
    assert not d.lights_on and not d.fan_on and d.hvac_mode == "off"


def test_fw_centre_percent():
    d = fw_dial.DialState(brightness=65)
    assert d.centre_percent() == 65
    d.apply("press")
    d.apply("rotate", 3)
    assert d.centre_percent() == 100  # fan 3/3


def test_hub_dial_event_matches_firmware(store):
    s = store.apply_dial_event("living", DialEvent(action="rotate", delta=3))
    assert s.brightness == 80 and s.lights_on  # 65 + 15
    s = store.apply_dial_event("living", DialEvent(action="press"))
    assert s.mode == DialMode.FAN
    s = store.apply_dial_event("living", DialEvent(action="rotate", delta=9))
    assert s.fan_speed == 3
    s = store.apply_dial_event("living", DialEvent(action="long_press"))
    assert not s.lights_on and s.fan_speed == 0 and s.hvac_mode == "off"


def test_clamps():
    assert fw_dial.clamp_brightness(250) == 100
    assert fw_dial.clamp_brightness(-5) == 0
    assert fw_dial.clamp_fan_speed(9) == 3
    assert fw_dial.clamp_temp_c(99) == 30.0
    assert fw_dial.clamp_temp_c(1) == 16.0

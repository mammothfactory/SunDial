"""SunDial MicroPython entry point — M5Stack Dial v1.1.

Wiring (verified, see docs/HARDWARE.md):
  encoder GPIO40/41, button GPIO42, buzzer GPIO3, power-hold GPIO46,
  display GC9A01 240x240, touch FT3267, RTC BM8563, RFID WS1850S.

Flow: hold power -> connect Wi-Fi -> poll hub state -> rotary/button
events update DialState, redraw the round UI, and POST to the hub.
Long-press the dial (button held >1.5 s) turns the whole room off.

Requires: MicroPython for ESP32-S3, a GC9A01 driver and an FT3267
touch driver (e.g. micropython-gc9a01). UNTESTED ON REAL HARDWARE here —
see firmware/esphome/m5dial.yaml for the proven ESPHome fallback.
"""
try:
    from machine import Pin  # type: ignore[import]
    import utime as time  # type: ignore[import]
    _ON_DEVICE = True
except ImportError:
    import time
    Pin = None
    _ON_DEVICE = False

from config import CONFIG
from dial import DialState
from net import HubClient, connect_wifi
from ui import DialUI

ENCODER_A = 40
ENCODER_B = 41
BUTTON = 42
BUZZER = 3
POWER_HOLD = 46


def beep(duration_ms=50):
    if not _ON_DEVICE:
        return
    try:
        pin = Pin(BUZZER, Pin.OUT)
        pin.on()
        time.sleep_ms(duration_ms)
        pin.off()
    except Exception:
        pass


def main():
    state = DialState()
    ui = DialUI(display=None)  # pass a GC9A01 display object here on-device
    hub = HubClient(CONFIG["hub_url"], CONFIG["room_id"])
    if _ON_DEVICE:
        Pin(POWER_HOLD, Pin.OUT).on()
        connect_wifi(CONFIG["wifi_ssid"], CONFIG["wifi_password"])
        ui.render(state, CONFIG["room_name"])
        # Encoder/button interrupt handlers would be attached here:
        #   Pin(ENCODER_A/B) -> state.apply("rotate", +/-1)
        #   Pin(BUTTON) short press -> state.apply("press")
        #                    tap on screen -> state.apply("tap")
        #                    hold >1.5 s  -> state.apply("long_press")
        # Each event: beep(), ui.render(...), hub.post_event(event).
        while True:
            time.sleep(5)
            try:
                hub_state = hub.get_state()
                state.brightness = hub_state.get("brightness", state.brightness)
                state.target_temp_c = hub_state.get("target_temp_c", state.target_temp_c)
                ui.render(state, CONFIG["room_name"])
            except Exception:
                pass
    return state, ui, hub


if __name__ == "__main__":
    main()

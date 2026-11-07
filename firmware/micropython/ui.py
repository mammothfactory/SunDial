"""SunDial round UI for the 1.28\" 240x240 GC9A01 display.

Palette (from the SunDial concept): deep green #0B2E2B, panel #123B36,
gold #D9A441, burnt-orange ring #C65A2E, cream #F5EFE6.
Layout: centre % in large cream text, mode label in gold underneath,
an orange arc ring showing the % around the edge, room name at top.

Hardware note: requires a GC9A01 driver (e.g. micropython-gc9a01) and an
FT3267 touch driver on MicroPython for ESP32-S3. This module degrades
gracefully — if no display driver is present it keeps a text framebuffer
so the logic can be exercised on a host. UNTESTED ON REAL HARDWARE here.
"""
# Palette as 16-bit RGB565 values (GC9A01 native format).
GREEN = 0x092E  # approx #0B2E2B
PANEL = 0x0F3B  # approx #123B36
GOLD = 0xD5A0   # approx #D9A441
ORANGE = 0xC2A8  # approx #C65A2E
CREAM = 0xFFD6  # approx #F5EFE6
BLACK = 0x0000

WIDTH = 240
HEIGHT = 240


def arc_end_angle(percent):
    """Sweep of the orange ring, 0-100% -> 0-270 degrees, starting at 135 deg."""
    return int(135 + percent / 100.0 * 270)


class DialUI:
    def __init__(self, display=None):
        self.display = display
        self.last_frame = {}

    def render(self, state, room_name="Living"):
        """Draw one frame. `state` is a DialState (dial.py)."""
        pct = state.centre_percent()
        frame = {
            "room": room_name,
            "mode": state.mode,
            "centre_percent": pct,
            "centre_label": "SUNDIAL",
            "ring_end_angle": arc_end_angle(pct),
            "lights_on": state.lights_on,
            "fan_speed": state.fan_speed,
            "target_temp_c": state.target_temp_c,
        }
        self.last_frame = frame
        if self.display is None:
            return frame
        try:
            d = self.display
            d.fill(GREEN)
            d.circle(120, 120, 108, ORANGE)
            # Centre value + label; exact text calls depend on the driver.
            d.text(str(pct) + "%", 105, 110, CREAM)
            d.text("SUNDIAL", 100, 130, GOLD)
            d.text(room_name, 95, 30, GOLD)
            d.text(state.mode.upper(), 100, 160, CREAM)
        except Exception:
            pass
        return frame

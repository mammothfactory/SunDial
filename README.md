# SunDial

> **Meet SunDial. A familiar touch. In every room.**

Sundello's integrated home lighting and fan control concept, built for
real hardware: one round wall dial in every room that lets you select
**Lights**, **Fan**, or **HVAC**, then adjust with a turn. A companion
app keeps the same rooms in hand — **Living, Bedroom, Kitchen** in the
demo — and lights and fans stay in sync across dial, app, and Home
Assistant.

Design: deep dark green (`#0B2E2B` / `#123B36`), gold (`#D9A441`),
burnt-orange ring (`#C65A2E`), cream text (`#F5EFE6`). The dial shows a
% in the centre with **SUNDIAL** underneath.

## Hardware

**M5Stack Dial v1.1** — $34.90 —
https://shop.m5stack.com/products/m5stack-dial-v1-1

ESP32-S3FN8 dual-core @ 240 MHz, 8 MB flash, 2.4 GHz Wi-Fi, 1.28"
round TFT 240×240 (GC9A01), touch (FT3267), rotary encoder
(GPIO40/41, 16 positions / 64 pulses per rev), RFID WS1850S, RTC
BM8563, buzzer (GPIO3), button (GPIO42), Port A I2C (G13/G15),
Port B GPIO (G1/G2), DC 6–36 V input, USB-C 5 V, 5 V @ 88.19 mA,
51.0 × 51.0 × 32.3 mm. Full specs: `docs/HARDWARE.md`.

**PoE — the honest bit:** the Dial has no native PoE or Ethernet. PoE
is via a certified 802.3af/at splitter at the wall: PoE switch → Cat6
→ splitter → 5 V USB-C into the Dial (or 12 V into the 6–36 V DC
terminal). One cable for power; data stays on Wi-Fi. One dial is
~0.44 W, so a houseful is a few watts. Details, parts list, and safety
notes: `docs/POE-WIRING.md`.

## Quickstart (demo mode, no Home Assistant needed)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
HASS_DEMO=true uvicorn hub.app.main:app --port 8000
# open http://127.0.0.1:8000
```

```bash
# simulator — the whole loop with no hardware
python simulator/dial_sim.py --demo
python simulator/dial_sim.py --room bedroom   # interactive
```

## How it works

| Gesture | Effect |
|---|---|
| Rotate | Adjust current mode: Lights ±5 %/detent, Fan ±1 speed, HVAC ±0.5 °C/detent |
| Press | Next mode: Lights → Fan → HVAC → Lights |
| Tap | Toggle current mode on/off |
| Long-press | Everything in the room off |

The dial POSTs to `POST /rooms/{room_id}/dial/event`; the hub applies
it, forwards to Home Assistant, and broadcasts state over WebSocket, so
dial and companion app stay in sync.

## Rooms (demo)

| Room | Dial | PoE port | Lights | Fan | HVAC |
|---|---|---|---|---|---|
| Living | sundial-living-01 | 3 | light.living_room | fan.living_room | climate.living_room |
| Bedroom | sundial-bedroom-01 | 4 | light.bedroom | fan.bedroom | climate.bedroom |
| Kitchen | sundial-kitchen-01 | 5 | light.kitchen | fan.kitchen | climate.kitchen |

Edit `config/rooms.yaml` for your home (see `config/rooms.example.yaml`).

## Repo layout

```
hub/                    Python FastAPI hub (REST + WebSocket + companion)
  app/main.py           endpoints, WebSocket broadcast, static serving
  app/models.py         Pydantic models + clamping (brightness 0-100,
                        fan 0-3, HVAC 16-30 C)
  app/state.py          in-memory room state + dial-event handling
  app/rooms.py          config/rooms.yaml loader
  app/homeassistant.py  HA REST client (demo mode needs no HA)
  app/mqtt.py           optional MQTT publish (sundial/room/<id>/state)
firmware/micropython/   MicroPython firmware for the Dial (Python path)
firmware/esphome/       ESPHome fallback config (same 3 modes)
companion/              web companion app (static HTML/CSS/JS, no build)
simulator/              terminal dial simulator
scripts/provision.py    per-room firmware config + checklist generator
config/                 rooms.yaml (demo) + rooms.example.yaml
docs/                   ARCHITECTURE, POE-WIRING, INSTALL, HARDWARE
tests/                  pytest: config, dial state machine, hub endpoints
```

## Real Home Assistant

```bash
export HASS_DEMO=false HA_URL=http://homeassistant.local:8123 HA_TOKEN=<token>
```

## Status / limits

- Hub, companion app, simulator, and tests are verified here (see below).
- MicroPython firmware is **untested on real hardware** — it needs
  GC9A01 + FT3267 drivers on the Dial. The ESPHome config is the proven
  fallback and is **not compiled** here; run `esphome compile` to check it.
- Tests: `pytest -q` (20 tests, all passing).

## License

MIT — see `LICENSE`.

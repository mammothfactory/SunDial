# Architecture

```
                ┌──────────────┐  Wi-Fi 2.4 GHz   ┌──────────────────┐
  Wall dial     │ M5Stack Dial │ ───────────────► │  SunDial hub     │
  (per room)    │  v1.1 240×240│  REST / WS       │  Python + FastAPI│
                │  MicroPython │ ◄─────────────── │  config/rooms.yaml│
                │  or ESPHome  │  state           │  HA client / MQTT│
                └──────────────┘                  └──────┬───────────┘
                                                         │ REST / WS
                                                  ┌──────▼───────────┐
                                                  │ Companion web app│
                                                  │ (companion/,     │
                                                  │  served by hub)  │
                                                  └──────────────────┘
                                                         │ HA REST API
                                                  ┌──────▼───────────┐
                                                  │ Home Assistant   │
                                                  │ (optional; demo  │
                                                  │  mode needs none)│
                                                  └──────────────────┘
```

## Components

- **hub/** — Python 3.11+ FastAPI app. Loads `config/rooms.yaml`
  (Living, Bedroom, Kitchen in the demo), holds in-memory room state,
  exposes REST + WebSocket, and serves the companion app. `HASS_DEMO=true`
  (default) runs with no Home Assistant: the in-memory store is the
  backend. Set `HASS_DEMO=false`, `HA_URL`, `HA_TOKEN` to drive real
  `light.*` / `fan.*` / `climate.*` entities.
- **firmware/micropython/** — the Python-on-device path: `dial.py` is the
  mode state machine, `ui.py` draws the round 240×240 UI, `net.py` talks
  to the hub. Requires GC9A01 + FT3267 MicroPython drivers. Untested on
  real hardware here.
- **firmware/esphome/m5dial.yaml** — proven ESPHome fallback for the same
  three modes, using the verified pins in `HARDWARE.md`. Not compiled here.
- **companion/** — static HTML/CSS/JS, no build step, served by the hub
  at `/`. Same rooms, same modes, synced over REST + WebSocket.
- **simulator/dial_sim.py** — terminal dial: rotate/press/tap against the
  hub, no hardware needed.

## Interaction contract (one dial, one room)

| Gesture | Effect |
|---|---|
| Rotate | Adjust current mode: Lights ±5 %/detent, Fan ±1 speed, HVAC ±0.5 °C/detent |
| Press (dial button) | Next mode: Lights → Fan → HVAC → Lights |
| Tap (touch) | Toggle current mode on/off |
| Long-press | Everything in the room off (lights off, fan off, HVAC off) |

The dial POSTs `{mode, delta, action}` to
`POST /rooms/{room_id}/dial/event`; the hub applies it, forwards to Home
Assistant, publishes MQTT (`sundial/room/<id>/state`, if `MQTT_BROKER`
is set), and broadcasts the new state to WebSocket subscribers. The
companion app and the dial therefore always show the same state.

## State & limits

- Brightness 0–100 %, fan speed 0–3, HVAC target 16–30 °C — clamped in
  `hub/app/models.py` and mirrored in `firmware/micropython/dial.py`.
- The hub keeps an in-memory mirror of each room even with real HA, so a
  brief HA outage does not blank the dials.

# Install

## 1. Hub (demo mode — no Home Assistant needed)

```bash
git clone <your SunDial repo URL>
cd SunDial
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
HASS_DEMO=true uvicorn hub.app.main:app --port 8000
```

Open http://127.0.0.1:8000 — the companion app (Living / Bedroom /
Kitchen). Try it:

```bash
curl http://127.0.0.1:8000/rooms/living/state
curl -X POST http://127.0.0.1:8000/rooms/living/lights \
  -H 'Content-Type: application/json' -d '{"brightness": 80}'
```

## 2. Simulator (no hardware)

```bash
python simulator/dial_sim.py --demo            # scripted sequence
python simulator/dial_sim.py --room bedroom    # interactive: + - p t l s q
```

## 3. Real Home Assistant

```bash
export HASS_DEMO=false HA_URL=http://homeassistant.local:8123 \
  HA_TOKEN=<long-lived access token>
```

Edit `config/rooms.yaml` so each room's `light.*` / `fan.*` /
`climate.*` entity ids match your HA instance, then restart the hub.
Optional MQTT state publish: set `MQTT_BROKER` (and `MQTT_PORT`, default
1883); without it, MQTT is simply skipped.

## 4. Flash a dial

```bash
python scripts/provision.py --room living --hub-url http://192.168.1.10:8000
# -> out/living/config.json, out/living/sundial-living-01.yaml, out/living/CHECKLIST.md
```

- **MicroPython path:** flash MicroPython for ESP32-S3, copy
  `firmware/micropython/*.py` + the generated `config.json` to the Dial,
  install a GC9A01 driver and an FT3267 touch driver. Untested on real
  hardware here.
- **ESPHome path (proven):** `esphome run out/living/sundial-living-01.yaml`
  with `wifi_ssid` / `wifi_password` in `secrets.yaml`. Not compiled here.

## 5. Power it

One Cat6 run per room from an 802.3af/at PoE switch to a certified
splitter at the wall, 5 V USB-C into the Dial. See `docs/POE-WIRING.md`.

## Tests

```bash
pytest -q
```

"""SunDial provisioning CLI.

Reads config/rooms.yaml and, per room, generates:
  - firmware/micropython/config.json (Wi-Fi + hub URL + room id)
  - a per-room ESPHome yaml from firmware/esphome/m5dial.yaml
  - a provisioning checklist (flash command, PoE splitter check)

Usage:
    python scripts/provision.py --room living --hub-url http://192.168.1.10:8000
    python scripts/provision.py --all --out out/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hub.app.rooms import load_rooms  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def provision_room(room, hub_url: str, wifi_ssid: str, out: Path) -> list[Path]:
    room_dir = out / room.id
    room_dir.mkdir(parents=True, exist_ok=True)
    cfg = {
        "room_id": room.id, "room_name": room.name, "dial_id": room.dial_id,
        "wifi_ssid": wifi_ssid, "wifi_password": "SET_ON_DEVICE",
        "hub_url": hub_url, "mqtt_broker": "",
    }
    cfg_path = room_dir / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    template = (ROOT / "firmware" / "esphome" / "m5dial.yaml").read_text(encoding="utf-8")
    yaml_text = (template.replace("room_id: living", f"room_id: {room.id}")
                 .replace("room_name: Living", f"room_name: {room.name}")
                 .replace("device_name: sundial-living-01", f"device_name: {room.dial_id}"))
    yaml_path = room_dir / f"{room.dial_id}.yaml"
    yaml_path.write_text(yaml_text, encoding="utf-8")

    checklist = f"""# SunDial provisioning — {room.name} ({room.id})
Dial: {room.dial_id} · PoE switch port: {room.poe_switch_port or '—'}

- [ ] PoE: 802.3af/at splitter at the wall, 5V USB-C into the Dial
      (or 12V into the 6-36V DC terminal). Verify the Dial powers on.
- [ ] Flash MicroPython for ESP32-S3, copy firmware/micropython/*.py + config.json
      OR flash ESPHome: `esphome run {yaml_path.name}`
- [ ] Wi-Fi: set SSID/password in config.json (MicroPython) or secrets.yaml (ESPHome)
- [ ] Hub: {hub_url} reachable from the dial's Wi-Fi network
- [ ] Entities: lights {room.lights.entity_id}, fan {room.fan.entity_id},
      HVAC {room.hvac.entity_id}
- [ ] Test: rotate (brightness), press (next mode), tap (toggle), long-press (all off)
"""
    check_path = room_dir / "CHECKLIST.md"
    check_path.write_text(checklist, encoding="utf-8")
    return [cfg_path, yaml_path, check_path]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Provision SunDial dials")
    p.add_argument("--room", help="room id to provision")
    p.add_argument("--all", action="store_true")
    p.add_argument("--config", default=str(ROOT / "config" / "rooms.yaml"))
    p.add_argument("--hub-url", default="http://192.168.1.10:8000")
    p.add_argument("--wifi-ssid", default="YOUR_WIFI_SSID")
    p.add_argument("--out", default="out")
    args = p.parse_args(argv)
    rooms = load_rooms(args.config)
    selected = rooms if args.all else [r for r in rooms if r.id == args.room]
    if not selected:
        print(f"no room matched (use --room <id> or --all); rooms: {[r.id for r in rooms]}")
        return 2
    out = Path(args.out)
    for room in selected:
        paths = provision_room(room, args.hub_url, args.wifi_ssid, out)
        print(f"{room.id}: wrote " + ", ".join(str(p) for p in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

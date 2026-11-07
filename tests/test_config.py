from pathlib import Path

import pytest

from hub.app.models import RoomConfig
from hub.app.rooms import load_rooms

ROOT = Path(__file__).resolve().parents[1]


def test_demo_rooms_load():
    rooms = load_rooms(ROOT / "config" / "rooms.yaml")
    assert [r.id for r in rooms] == ["living", "bedroom", "kitchen"]
    assert rooms[0].dial_id == "sundial-living-01"
    assert rooms[0].poe_switch_port == 3


def test_example_matches_demo():
    assert load_rooms(ROOT / "config" / "rooms.example.yaml")


def test_duplicate_room_id_rejected(tmp_path):
    bad = tmp_path / "rooms.yaml"
    bad.write_text("rooms:\n"
                   "  - {id: living, name: Living, dial_id: a, lights: {entity_id: light.a}, fan: {entity_id: fan.a}, hvac: {entity_id: climate.a}}\n"
                   "  - {id: living, name: Living2, dial_id: b, lights: {entity_id: light.b}, fan: {entity_id: fan.b}, hvac: {entity_id: climate.b}}\n")
    with pytest.raises(ValueError, match="duplicate room"):
        load_rooms(bad)


def test_clamping_in_config():
    r = RoomConfig(id="x", name="X", dial_id="d",
                   lights={"entity_id": "light.x", "default_brightness": 250},
                   fan={"entity_id": "fan.x", "max_speed": 9},
                   hvac={"entity_id": "climate.x", "default_target_temp_c": 99})
    assert r.lights.default_brightness == 100
    assert r.fan.max_speed == 3
    assert r.hvac.default_target_temp_c == 30.0

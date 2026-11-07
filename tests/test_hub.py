from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hub.app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client():
    return TestClient(create_app(ROOT / "config" / "rooms.yaml"))


def test_health_and_rooms(client):
    assert client.get("/health").json()["status"] == "ok"
    rooms = client.get("/rooms").json()
    assert [r["id"] for r in rooms] == ["living", "bedroom", "kitchen"]


def test_unknown_room_404(client):
    assert client.get("/rooms/nope/state").status_code == 404


def test_lights_brightness_clamped(client):
    r = client.post("/rooms/living/lights", json={"brightness": 250})
    assert r.status_code == 200 and r.json()["brightness"] == 100
    assert r.json()["lights_on"] is True
    r = client.post("/rooms/living/lights", json={"brightness": 0})
    assert r.json()["lights_on"] is False


def test_fan_speed_clamped(client):
    r = client.post("/rooms/bedroom/fan", json={"speed": 9})
    assert r.json()["fan_speed"] == 3 and r.json()["fan_on"] is True


def test_hvac_temp_clamped(client):
    r = client.post("/rooms/kitchen/hvac", json={"target_temp_c": 99, "mode": "heat"})
    assert r.json()["target_temp_c"] == 30.0 and r.json()["hvac_mode"] == "heat"
    r = client.post("/rooms/kitchen/hvac", json={"target_temp_c": 1})
    assert r.json()["target_temp_c"] == 16.0


def test_dial_event_flow(client):
    r = client.post("/rooms/living/dial/event", json={"delta": 3, "action": "rotate"})
    assert r.json()["brightness"] == 80
    r = client.post("/rooms/living/dial/event", json={"action": "press"})
    assert r.json()["mode"] == "fan"


def test_press_with_post_action_mode_is_not_advanced_twice(client):
    # Firmware sends the mode AFTER its local state machine ran, so a
    # press that already moved lights -> fan must land on fan, not hvac.
    r = client.post("/rooms/living/dial/event",
                    json={"mode": "fan", "delta": 0, "action": "press"})
    assert r.json()["mode"] == "fan"
    r = client.post("/rooms/living/dial/event",
                    json={"mode": "fan", "delta": 1, "action": "rotate"})
    assert r.json()["fan_speed"] == 1 and r.json()["mode"] == "fan"


def test_companion_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "SunDial" in r.text
    assert client.get("/static/style.css").status_code == 200


def test_websocket_state(client):
    with client.websocket_connect("/ws/living") as ws:
        first = ws.receive_json()
        assert first["room_id"] == "living"

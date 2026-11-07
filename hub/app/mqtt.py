"""Optional MQTT publish helper. No broker is required: if MQTT_BROKER is
unset (the default) every call is a no-op, so the hub runs standalone.
"""
from __future__ import annotations

import json
import os


def publish_state(room_id: str, state: dict) -> bool:
    broker = os.environ.get("MQTT_BROKER", "")
    if not broker:
        return False
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        return False
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(broker, int(os.environ.get("MQTT_PORT", "1883")), 5)
        client.publish(f"sundial/room/{room_id}/state", json.dumps(state), retain=True)
        client.disconnect()
        return True
    except Exception:
        return False

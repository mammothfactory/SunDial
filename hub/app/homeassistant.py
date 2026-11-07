"""Home Assistant REST client. Demo mode (default) does nothing on the
wire — the in-memory RoomStore is the backend, so the hub, simulator and
tests work with no HA instance. Set HASS_DEMO=false with HA_URL + HA_TOKEN
to drive real entities.
"""
from __future__ import annotations

import os

import httpx


class HomeAssistantClient:
    def __init__(self, base_url: str | None = None, token: str | None = None,
                 demo: bool | None = None) -> None:
        self.demo = True if demo is None else demo
        if demo is None:
            self.demo = os.environ.get("HASS_DEMO", "true").lower() in ("1", "true", "yes")
        self.base_url = (base_url or os.environ.get("HA_URL", "")).rstrip("/")
        self.token = token or os.environ.get("HA_TOKEN", "")
        if not self.demo and (not self.base_url or not self.token):
            raise ValueError("HA_URL and HA_TOKEN are required when HASS_DEMO=false")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def call_service(self, domain: str, service: str, data: dict) -> dict | None:
        if self.demo:
            return None
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self._headers(), json=data)
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    def set_light(self, entity_id: str, on: bool, brightness: int | None = None) -> None:
        if self.demo:
            return
        data: dict = {"entity_id": entity_id}
        if on and brightness is not None:
            data["brightness_pct"] = brightness
        self.call_service("light", "turn_on" if on else "turn_off", data)

    def set_fan(self, entity_id: str, on: bool, speed: int | None = None) -> None:
        if self.demo:
            return
        if not on:
            self.call_service("fan", "turn_off", {"entity_id": entity_id})
            return
        data: dict = {"entity_id": entity_id}
        if speed is not None:
            data["percentage"] = int(speed / 3 * 100)
        self.call_service("fan", "turn_on", data)

    def set_hvac(self, entity_id: str, mode: str | None, target_temp_c: float | None = None) -> None:
        if self.demo:
            return
        if mode is not None:
            self.call_service("climate", "set_hvac_mode",
                              {"entity_id": entity_id, "hvac_mode": mode})
        if target_temp_c is not None:
            self.call_service("climate", "set_temperature",
                              {"entity_id": entity_id, "temperature": target_temp_c})

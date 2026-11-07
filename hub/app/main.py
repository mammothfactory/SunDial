"""SunDial hub — FastAPI app.

Serves the REST API, the WebSocket state feed, and the companion web app
in companion/ (static, no build step).

Run in demo mode (no Home Assistant needed):
    HASS_DEMO=true uvicorn hub.app.main:app --port 8000
    # or: python -m hub.app.main
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .homeassistant import HomeAssistantClient
from .models import DialEvent, FanRequest, HvacRequest, LightsRequest, RoomState
from .mqtt import publish_state
from .rooms import load_rooms
from .state import RoomStore

COMPANION_DIR = Path(__file__).resolve().parents[2] / "companion"


def create_app(config_path: str | Path | None = None) -> FastAPI:
    configs = load_rooms(config_path)
    store = RoomStore(configs)
    ha = HomeAssistantClient()
    app = FastAPI(title="SunDial", description="Meet SunDial. A familiar touch. In every room.")
    app.state.store = store
    app.state.configs = {c.id: c for c in configs}
    app.state.ha = ha
    subscribers: dict[str, set[WebSocket]] = {c.id: set() for c in configs}

    async def broadcast(room_id: str) -> None:
        state = store.get(room_id).model_dump(mode="json")
        publish_state(room_id, state)
        dead: list[WebSocket] = []
        for ws in list(subscribers.get(room_id, set())):
            try:
                await ws.send_text(json.dumps(state))
            except Exception:
                dead.append(ws)
        for ws in dead:
            subscribers[room_id].discard(ws)

    def room_or_404(room_id: str):
        if room_id not in app.state.configs:
            raise HTTPException(status_code=404, detail=f"unknown room: {room_id}")
        return app.state.configs[room_id]

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "rooms": len(configs), "demo": ha.demo}

    @app.get("/rooms")
    def list_rooms() -> list[dict]:
        return [c.model_dump() for c in configs]

    @app.get("/rooms/{room_id}")
    def get_room(room_id: str) -> dict:
        return room_or_404(room_id).model_dump()

    @app.get("/rooms/{room_id}/state", response_model=RoomState)
    def get_state(room_id: str) -> RoomState:
        room_or_404(room_id)
        return store.get(room_id)

    @app.post("/rooms/{room_id}/lights", response_model=RoomState)
    async def set_lights(room_id: str, req: LightsRequest) -> RoomState:
        cfg = room_or_404(room_id)
        state = store.set_lights(room_id, req.on, req.brightness)
        ha.set_light(cfg.lights.entity_id, state.lights_on, state.brightness)
        await broadcast(room_id)
        return state

    @app.post("/rooms/{room_id}/fan", response_model=RoomState)
    async def set_fan(room_id: str, req: FanRequest) -> RoomState:
        cfg = room_or_404(room_id)
        state = store.set_fan(room_id, req.on, req.speed)
        ha.set_fan(cfg.fan.entity_id, state.fan_on, state.fan_speed)
        await broadcast(room_id)
        return state

    @app.post("/rooms/{room_id}/hvac", response_model=RoomState)
    async def set_hvac(room_id: str, req: HvacRequest) -> RoomState:
        cfg = room_or_404(room_id)
        state = store.set_hvac(room_id, req.mode, req.target_temp_c)
        ha.set_hvac(cfg.hvac.entity_id, state.hvac_mode, state.target_temp_c)
        await broadcast(room_id)
        return state

    @app.post("/rooms/{room_id}/dial/event", response_model=RoomState)
    async def dial_event(room_id: str, event: DialEvent) -> RoomState:
        cfg = room_or_404(room_id)
        state = store.apply_dial_event(room_id, event)
        ha.set_light(cfg.lights.entity_id, state.lights_on, state.brightness)
        ha.set_fan(cfg.fan.entity_id, state.fan_on, state.fan_speed)
        ha.set_hvac(cfg.hvac.entity_id, state.hvac_mode, state.target_temp_c)
        await broadcast(room_id)
        return state

    @app.websocket("/ws/{room_id}")
    async def ws_room(websocket: WebSocket, room_id: str) -> None:
        if room_id not in subscribers:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        subscribers[room_id].add(websocket)
        await websocket.send_text(json.dumps(store.get(room_id).model_dump(mode="json")))
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            subscribers[room_id].discard(websocket)

    if COMPANION_DIR.exists():
        app.mount("/static", StaticFiles(directory=COMPANION_DIR), name="static")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(COMPANION_DIR / "index.html")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("hub.app.main:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", "8000")), reload=False)


if __name__ == "__main__":
    run()

"""Load and validate config/rooms.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import RoomConfig

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "rooms.yaml"


def load_rooms(path: str | Path | None = None) -> list[RoomConfig]:
    path = Path(path) if path else DEFAULT_CONFIG
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    rooms = data.get("rooms", [])
    if not rooms:
        raise ValueError(f"no rooms defined in {path}")
    configs = [RoomConfig(**room) for room in rooms]
    ids = [r.id for r in configs]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate room ids in {path}: {ids}")
    dial_ids = [r.dial_id for r in configs]
    if len(set(dial_ids)) != len(dial_ids):
        raise ValueError(f"duplicate dial_ids in {path}: {dial_ids}")
    return configs

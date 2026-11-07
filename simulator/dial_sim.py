"""SunDial terminal simulator — demo the whole loop with no hardware.

Usage:
    python simulator/dial_sim.py --hub http://127.0.0.1:8000 --room living
    python simulator/dial_sim.py --demo   # scripted rotate/press/tap sequence

Keys (interactive):  + / - rotate, p press (next mode), t tap (toggle),
l long-press (all off), s show state, q quit. Type a key + Enter.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "firmware" / "micropython"))
from dial import DialState  # noqa: E402


def _req(hub: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(hub.rstrip("/") + path, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def show(hub: str, room: str) -> dict:
    state = _req(hub, f"/rooms/{room}/state")
    print(f"[{room}] mode={state['mode']} lights={'on' if state['lights_on'] else 'off'} "
          f"{state['brightness']}% | fan={'on' if state['fan_on'] else 'off'} speed={state['fan_speed']} | "
          f"hvac={state['hvac_mode']} {state['target_temp_c']}C (now {state['current_temp_c']}C)")
    return state


def send(hub: str, room: str, local: DialState, action: str, delta: int = 0) -> dict:
    event = local.apply(action, delta)
    state = _req(hub, f"/rooms/{room}/dial/event", event)
    print(f"  -> {action} delta={delta} => mode={state['mode']} centre={state.get('centre_percent', '')}")
    return state


def demo(hub: str, room: str) -> None:
    local = DialState()
    show(hub, room)
    send(hub, room, local, "rotate", 3)   # lights 65 -> 80%
    send(hub, room, local, "press")       # -> fan
    send(hub, room, local, "rotate", 2)   # fan speed 0 -> 2
    send(hub, room, local, "press")       # -> hvac
    send(hub, room, local, "rotate", 1)   # target 21.5 -> 22.0 C
    send(hub, room, local, "tap")         # hvac off
    show(hub, room)


def interactive(hub: str, room: str) -> None:
    local = DialState()
    show(hub, room)
    print("Keys: +/- rotate, p press, t tap, l long-press, s state, q quit")
    while True:
        try:
            key = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if key == "q":
            break
        elif key == "+":
            send(hub, room, local, "rotate", 1)
        elif key == "-":
            send(hub, room, local, "rotate", -1)
        elif key == "p":
            send(hub, room, local, "press")
        elif key == "t":
            send(hub, room, local, "tap")
        elif key == "l":
            send(hub, room, local, "long_press")
        elif key == "s":
            show(hub, room)
        else:
            print("unknown key")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SunDial dial simulator")
    p.add_argument("--hub", default="http://127.0.0.1:8000")
    p.add_argument("--room", default="living")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args(argv)
    if args.demo:
        demo(args.hub, args.room)
    else:
        interactive(args.hub, args.room)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

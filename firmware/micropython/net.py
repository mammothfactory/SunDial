"""Wi-Fi + hub client for the Dial (MicroPython).

Connects to 2.4 GHz Wi-Fi, then POSTs dial events to the hub and polls
room state. On CPython (tests / simulator) the network calls raise
NotImplementedError unless a transport is injected — the hub is exercised
through its REST API instead.
"""
import json

try:
    import network  # type: ignore[import]
    import urequests  # type: ignore[import]
    import utime as time  # type: ignore[import]
    _ON_DEVICE = True
except ImportError:  # CPython
    import time
    network = None
    urequests = None
    _ON_DEVICE = False


def connect_wifi(ssid, password, timeout_s=20):
    if not _ON_DEVICE:
        raise NotImplementedError("connect_wifi only runs on the Dial (MicroPython)")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        deadline = time.time() + timeout_s
        while not wlan.isconnected() and time.time() < deadline:
            time.sleep(0.5)
    return wlan.isconnected()


class HubClient:
    def __init__(self, hub_url, room_id):
        self.hub_url = hub_url.rstrip("/")
        self.room_id = room_id

    def post_event(self, event):
        if not _ON_DEVICE:
            raise NotImplementedError("post_event only runs on the Dial (MicroPython)")
        url = "%s/rooms/%s/dial/event" % (self.hub_url, self.room_id)
        resp = urequests.post(url, json=event,
                              headers={"Content-Type": "application/json"})
        try:
            return resp.json()
        finally:
            resp.close()

    def get_state(self):
        if not _ON_DEVICE:
            raise NotImplementedError("get_state only runs on the Dial (MicroPython)")
        resp = urequests.get("%s/rooms/%s/state" % (self.hub_url, self.room_id))
        try:
            return resp.json()
        finally:
            resp.close()

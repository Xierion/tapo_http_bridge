#!/usr/bin/env python3
"""
tapo_http_bridge - a tiny HTTP wrapper around almottier/TapoP100 (PyP100)
so Moonraker can control a Tapo P100 smart plug via its generic
`type: http` power device.

Endpoints (all GET, all JSON):
  /status  -> {"status": "on"}  | {"status": "off"}
  /on      -> turns the plug on,  returns {"status": "on"}
  /off     -> turns the plug off, returns {"status": "off"}
  /toggle  -> flips the plug,     returns the new state

On any failure it returns HTTP 502 with {"status": "error", "error": "..."}.
"""
import json
import logging
import threading
from pathlib import Path

from flask import Flask, jsonify
from PyP100 import PyP100

CONFIG_PATH = Path(__file__).parent / "config.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("tapo-bridge")

app = Flask(__name__)

# The Tapo protocol / TP-Link auth doesn't like concurrent sessions from
# the same client, so serialize all requests to the plug through one lock.
_lock = threading.Lock()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Copy config.example.json to config.json "
            "and fill in your plug IP + Tapo account email/password."
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_plug() -> "PyP100.P100":
    cfg = load_config()
    # A fresh object per request is the simplest way to avoid dealing with
    # session/cookie expiry - the library re-authenticates internally.
    return PyP100.P100(cfg["ip"], cfg["email"], cfg["password"])


def state_str(device_info: dict) -> str:
    return "on" if device_info.get("device_on") else "off"


@app.route("/status", methods=["GET"])
def status():
    with _lock:
        try:
            plug = get_plug()
            info = plug.getDeviceInfo()
            return jsonify(status=state_str(info))
        except Exception as e:
            log.exception("status check failed")
            return jsonify(status="error", error=str(e)), 502


@app.route("/on", methods=["GET"])
def turn_on():
    with _lock:
        try:
            plug = get_plug()
            plug.turnOn()
            return jsonify(status="on")
        except Exception as e:
            log.exception("turn on failed")
            return jsonify(status="error", error=str(e)), 502


@app.route("/off", methods=["GET"])
def turn_off():
    with _lock:
        try:
            plug = get_plug()
            plug.turnOff()
            return jsonify(status="off")
        except Exception as e:
            log.exception("turn off failed")
            return jsonify(status="error", error=str(e)), 502


@app.route("/toggle", methods=["GET"])
def toggle():
    with _lock:
        try:
            plug = get_plug()
            info = plug.getDeviceInfo()
            if state_str(info) == "on":
                plug.turnOff()
                return jsonify(status="off")
            plug.turnOn()
            return jsonify(status="on")
        except Exception as e:
            log.exception("toggle failed")
            return jsonify(status="error", error=str(e)), 502


if __name__ == "__main__":
    # Bind to localhost only - Moonraker runs on the same Pi, and this
    # server holds your Tapo account password in memory / in config.json.
    # Change host="0.0.0.0" only if you understand the exposure, and put
    # it behind a firewall / auth proxy if you do.
    app.run(host="127.0.0.1", port=5111)

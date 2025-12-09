from flask import Blueprint, request, jsonify
import time
import random

arduino_api = Blueprint("arduino_api", __name__)

last_rfid = None
last_pir = 0

@arduino_api.route("/esp8266/update", methods=["POST"])
def esp8266_update():
    """
    ESP8266 gửi dữ liệu y như thật:
    {
        "pir": 1 or 0,
        "rfid": "PET1234" or None
    }
    """
    global last_rfid, last_pir

    data = request.json
    last_pir = data.get("pir", 0)
    last_rfid = data.get("rfid", None)

    return jsonify({"status": "ok", "received": data})


@arduino_api.route("/esp8266/status", methods=["GET"])
def esp8266_status():
    return jsonify({
        "pir": last_pir,
        "rfid": last_rfid,
        "timestamp": time.time()
    })

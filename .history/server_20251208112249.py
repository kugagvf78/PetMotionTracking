from flask import Flask, render_template, Response, jsonify, request
import cv2
import os
from arduino_sim import ArduinoSimulator

app = Flask(__name__)
arduino = ArduinoSimulator()

camera = cv2.VideoCapture(0)


def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings():
    return render_template("settings.html", sensitivity=arduino.sensitivity,
                           log_enabled=arduino.log_enabled)


@app.route("/update-settings", methods=["POST"])
def update_settings():
    sensitivity = request.form.get("sensitivity")
    log_enabled = request.form.get("log_enabled") == "true"

    arduino.update_settings(sensitivity, log_enabled)

    return jsonify({"status": "success"})


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/get_logs")
def get_logs():
    if not os.path.exists("motion_log.txt"):
        return jsonify([])

    with open("motion_log.txt", "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs)


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
import os
from arduino_sim import ArduinoSimulator

app = Flask(__name__)
arduino = ArduinoSimulator()

# ==========================
# GLOBAL CAMERA HANDLING
# ==========================

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

latest_frame = None
lock = threading.Lock()

def camera_thread():
    global latest_frame, camera

    while True:
        if not camera.isOpened():
            print("⚠ Camera closed, reopening...")
            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            time.sleep(1)
            continue

        ret, frame = camera.read()

        if not ret or frame is None:
            print("⚠ Frame error, retrying...")
            time.sleep(0.1)
            continue

        with lock:
            latest_frame = frame

        time.sleep(0.03)  # giảm tải CPU (≈30 FPS)


# Start camera thread
threading.Thread(target=camera_thread, daemon=True).start()


# ==========================
# STREAM TO WEB
# ==========================

def gen_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            print("⚠ Chưa có frame → chờ camera")
            time.sleep(0.1)
            continue

        with lock:
            frame = latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            print("⚠ Encode lỗi")
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ==========================
# UI ROUTES
# ==========================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/settings")
def settings():
    return render_template("settings.html",
                           sensitivity=arduino.sensitivity,
                           log_enabled=arduino.log_enabled)

@app.route("/update-settings", methods=["POST"])
def update_settings():
    sensitivity = request.form.get("sensitivity")
    log_enabled = request.form.get("log_enabled") == "true"

    arduino.update_settings(sensitivity, log_enabled)
    return jsonify({"status": "success"})


# ==========================
# READ LOGS
# ==========================

@app.route("/get_logs")
def get_logs():
    if not os.path.exists("motion_log.txt"):
        return jsonify([])

    with open("motion_log.txt", "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs)


# ==========================
# RUN FLASK
# ==========================

if __name__ == "__main__":
    print("🚀 Server Flask chạy tại http://127.0.0.1:5000")
    app.run(debug=True)

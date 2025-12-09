from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ======== CAMERA SETUP =========
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
latest_frame = None
lock = threading.Lock()


def camera_loop():
    global latest_frame

    while True:
        if not camera.isOpened():
            print("⚠️ Camera chưa mở được")
            time.sleep(1)
            continue

        ret, frame = camera.read()
        if not ret:
            print("⚠️ Không đọc được frame")
            time.sleep(0.1)
            continue

        with lock:
            latest_frame = frame.copy()

        time.sleep(0.03)


# Start camera thread
threading.Thread(target=camera_loop, daemon=True).start()


# ===== STREAM VIDEO =====
def gen_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            continue

        with lock:
            frame = latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ===== HOME PAGE =====
@app.route("/")
def index():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w", encoding="utf-8").close()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return render_template("index.html", logs=logs)


# ===== API CHECK CAMERA =====
@app.route("/camera_status")
def camera_status():
    status = camera.isOpened()
    return jsonify({"status": "active" if status else "inactive"})


if __name__ == "__main__":
    print("🚀 Server chạy tại http://127.0.0.1:5000")
    app.run(debug=True)

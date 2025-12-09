from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
import os
from datetime import datetime
from arduino_sim import ArduinoSimulator

app = Flask(__name__)
arduino = ArduinoSimulator()

LOG_FILE = "motion_log.txt"

# ================================
# CAMERA THREAD
# ================================
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
camera.set(cv2.CAP_PROP_FPS, 30)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

latest_frame = None
last_gray = None

def camera_loop():
    global latest_frame, last_gray

    while True:
        ret, frame = camera.read()
        if not ret:
            print("⚠️ Không lấy được frame từ camera!")
            time.sleep(0.1)
            continue

        # =========================
        # Motion Detection
        # =========================
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_gray is None:
            last_gray = gray
        else:
            diff = cv2.absdiff(last_gray, gray)
            thresh = cv2.threshold(diff, arduino.sensitivity, 255, cv2.THRESH_BINARY)[1]

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in contours:
                if cv2.contourArea(c) < 800:
                    continue
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                log_motion()
                break

            last_gray = gray

        latest_frame = frame
        time.sleep(0.03)  # giảm tải CPU


# BẮT ĐẦU camera thread
t = threading.Thread(target=camera_loop, daemon=True)
t.start()

# ================================
# LOG FUNCTION
# ================================
def log_motion():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w", encoding="utf-8").close()

    msg = f"{datetime.now().strftime('%H:%M:%S')} - Chuyển động được ghi nhận!"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

    print("📌 LOG:", msg)


# ================================
# STREAM VIDEO
# ================================
def gen_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            continue

        ret, buffer = cv2.imencode(".jpg", latest_frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return jsonify([line.strip() for line in f])


if __name__ == "__main__":
    print("🚀 Server chạy tại: http://127.0.0.1:5000")
    app.run(debug=True)

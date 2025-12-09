from flask import Flask, render_template, Response, jsonify, request
import cv2
import os
from datetime import datetime
from arduino_sim import ArduinoSimulator

app = Flask(__name__)
arduino = ArduinoSimulator()

# -------------------------
# CAMERA INIT
# -------------------------
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

LOG_FILE = "motion_log.txt"

# -------------------------
# FUNCTION: GHI LOG
# -------------------------
def log_motion():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w", encoding="utf-8").close()

    time_stamp = datetime.now().strftime("%H:%M:%S")
    msg = f"{time_stamp} - Chuyển động được ghi nhận!"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

    print("📌 LOG:", msg)

# -------------------------
# FUNCTION: STREAM CAMERA + DETECT MOTION
# -------------------------
last_frame = None

def gen_frames():
    global last_frame

    while True:
        success, frame = camera.read()
        if not success:
            continue

        # ---- Motion Detection ----
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_frame is None:
            last_frame = gray
        else:
            diff = cv2.absdiff(last_frame, gray)
            thresh = cv2.threshold(diff, arduino.sensitivity, 255, cv2.THRESH_BINARY)[1]

            # tìm vùng chuyển động
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) < 800:   # giảm noise
                    continue

                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                log_motion()
                break

            last_frame = gray

        # ---- Stream frame ----
        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/settings")
def settings():
    return render_template("settings.html", sensitivity=arduino.sensitivity, log_enabled=arduino.log_enabled)

@app.route("/update-settings", methods=["POST"])
def update_settings():
    sens = int(request.form.get("sensitivity"))
    log_enabled = request.form.get("log_enabled") == "true"

    arduino.update_settings(sens, log_enabled)
    return jsonify({"status": "updated"})

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs)

# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    print("🚀 Flask Motion Tracking đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True)
    
from flask import Flask, render_template, Response, jsonify, request
import cv2
import os
from datetime import datetime
from arduino_sim import ArduinoSimulator
from camera_stream import CameraStream

# ----------------------------------------
# APP SETUP
# ----------------------------------------
app = Flask(__name__)
arduino = ArduinoSimulator()

# Camera dùng thread (ổn định nhất)
camera = CameraStream()

last_frame_gray = None


# ----------------------------------------
# VIDEO STREAM + MOTION DETECTION
# ----------------------------------------
def gen_frames():
    global last_frame_gray

    while True:
        frame = camera.read()
        if frame is None:
            continue

        # ============================
        # Motion Detection
        # ============================
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_frame_gray is None:
            last_frame_gray = gray
        else:
            diff = cv2.absdiff(last_frame_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]

            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                if cv2.contourArea(contour) < arduino.sensitivity:
                    continue

                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                timestamp = datetime.now().strftime("%H:%M:%S")
                arduino.receive_signal(f"{timestamp} - Chuyển động được ghi nhận")

            last_frame_gray = gray

        # ============================
        # Encode frame
        # ============================
        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


# ----------------------------------------
# ROUTES
# ----------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings():
    return render_template(
        "settings.html",
        sensitivity=arduino.sensitivity,
        log_enabled=arduino.log_enabled,
    )


@app.route("/update-settings", methods=["POST"])
def update_settings():
    sensitivity = int(request.form.get("sensitivity"))
    log_enabled = request.form.get("log_enabled") == "true"

    arduino.update_settings(sensitivity, log_enabled)

    return jsonify({"status": "success"})


@app.route("/video_feed")
def video_feed():
    return Response(
        gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/get_logs")
def get_logs():
    if not os.path.exists("motion_log.txt"):
        return jsonify([])

    with open("motion_log.txt", "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs)


# ----------------------------------------
# RUN APP
# ----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

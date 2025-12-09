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

    motion_counter = 0   # Chỉ báo khi phát hiện liên tục

    while True:
        frame = camera.read()
        if frame is None:
            continue

        # Bỏ qua frame đen
        if frame.mean() < 5:
            print("⚠ Frame đen, bỏ qua...")
            continue

        # Convert grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_frame_gray is None:
            last_frame_gray = gray
            continue  # Lần đầu không detect được

        # Tính độ khác biệt giữa 2 frame
        diff = cv2.absdiff(last_frame_gray, gray)
        thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)[1]

        # Loại nhiễu bằng morphological operations
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        movement_detected = False

        for contour in contours:
            if cv2.contourArea(contour) < max(arduino.sensitivity, 1500):
                continue

            movement_detected = True

            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # PHÁT HIỆN CHUYỂN ĐỘNG: nếu có >= 3 frame liên tiếp
        if movement_detected:
            motion_counter += 1
        else:
            motion_counter = 0

        if motion_counter >= 3:
            timestamp = datetime.now().strftime("%H:%M:%S")
            arduino.receive_signal(f"{timestamp} - Chuyển động được ghi nhận")
            motion_counter = 0   # Reset counter để tránh spam

        last_frame_gray = gray

        # Encode JPEG
        ret, buffer = cv2.imencode(".jpg", frame)
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

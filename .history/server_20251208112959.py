from flask import Flask, render_template, Response, jsonify, request
import cv2
import os
import time
from arduino_sim import ArduinoSimulator

app = Flask(__name__)
arduino = ArduinoSimulator()

# Mở camera 1 lần
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Biến dùng cho motion detection
last_frame = None


# ----- LIVE CAMERA + MOTION DETECTION -----
def gen_frames():
    global last_frame

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Convert để detect motion
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_frame is None:
            last_frame = gray
        else:
            diff = cv2.absdiff(last_frame, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) < arduino.sensitivity:
                    continue

                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

                # Gửi tín hiệu đến Arduino mô phỏng
                arduino.receive_signal("Chuyển động được ghi nhận")

            last_frame = gray

        # Encode frame -> gửi về web
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ----- MAIN PAGES -----
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings():
    return render_template("settings.html",
                           sensitivity=arduino.sensitivity,
                           log_enabled=arduino.log_enabled)


# ----- API: GET LOGS -----
@app.route("/get_logs")
def get_logs():
    if not os.path.exists("motion_log.txt"):
        return jsonify([])
    with open("motion_log.txt", "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]
    return jsonify(logs)


# ----- API: UPDATE ARDUINO SETTINGS -----
@app.route("/update-settings", methods=["POST"])
def update_settings():
    sensitivity = request.form.get("sensitivity")
    log_enabled = request.form.get("log_enabled") == "true"
    arduino.update_settings(sensitivity, log_enabled)
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(debug=True)

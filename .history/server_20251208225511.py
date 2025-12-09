from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
import os
from datetime import datetime
from ultralytics import YOLO

# ==================================================
# FLASK APP
# ==================================================
app = Flask(__name__)
LOG_FILE = "motion_log.txt"

# ==================================================
# LOAD YOLO COCO MODEL
# ==================================================
PET_MODEL = YOLO("yolov8n.pt")
PET_THRESHOLD = 0.25

# ==================================================
# GLOBAL SENSOR STATES (updated by ESP8266)
# ==================================================
last_pir = 0          # 0 = no motion, 1 = motion
last_rfid = None      # RFID tag ID
pet_detected_flag = False
behavior_score = 0

# ==================================================
# CAMERA SYSTEM
# ==================================================
camera = None
latest_frame = None
camera_lock = threading.Lock()
last_gray = None


def init_camera():
    """Try different backends."""
    global camera

    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (0, "Default")
    ]

    for backend, name in backends:
        try:
            cam = cv2.VideoCapture(0, backend) if backend != 0 else cv2.VideoCapture(0)

            if cam.isOpened():
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera = cam
                print(f"📷 Camera started via {name}")
                return
        except:
            continue

    print("❌ No camera available")


# ==================================================
# LOGGING HELPERS
# ==================================================
def write_log(text):
    msg = f"{datetime.now().strftime('%H:%M:%S')} - {text}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print("📌 LOG:", msg)


def log_pir():
    write_log("PIR: phát hiện chuyển động (Arduino)")


def log_rfid(tag):
    write_log(f"RFID: quét thẻ {tag}")


def log_pet(label, conf):
    write_log(f"Phát hiện thú cưng: {label} ({conf:.2f})")


# ==================================================
# CAMERA LOOP THREAD
# ==================================================
def camera_loop():
    global latest_frame, last_gray, camera
    global pet_detected_flag, behavior_score

    while True:
        if camera is None or not camera.isOpened():
            init_camera()
            time.sleep(1)
            continue

        ret, frame = camera.read()
        if not ret:
            time.sleep(0.1)
            continue

        # -------- Motion Detection -------- #
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_gray is None:
            last_gray = gray
        else:
            diff = cv2.absdiff(last_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in contours:
                if cv2.contourArea(c) > 800:
                    write_log("Chuyển động (Camera)")
                    behavior_score = min(100, behavior_score + 5)
                    break

            last_gray = gray

        # -------- YOLO Pet Detection -------- #
        pet_detected_flag = False
        results = PET_MODEL.predict(frame, conf=PET_THRESHOLD, verbose=False)

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = PET_MODEL.names[cls]

                if label not in ["dog", "cat"]:
                    continue

                if conf >= PET_THRESHOLD:
                    pet_detected_flag = True
                    log_pet(label, conf)

        # -------- Store frame for streaming -------- #
        with camera_lock:
            latest_frame = frame.copy()

        time.sleep(0.03)


# ==================================================
# ESP8266 PIR & RFID API
# ==================================================
@app.route("/update_pir", methods=["POST"])
def update_pir():
    global last_pir
    data = request.json
    last_pir = int(data.get("pir", 0))

    if last_pir == 1:
        log_pir()

    return jsonify({"status": "ok", "pir": last_pir})


@app.route("/update_rfid", methods=["POST"])
def update_rfid():
    global last_rfid
    data = request.json
    last_rfid = data.get("rfid", None)

    if last_rfid:
        log_rfid(last_rfid)

    return jsonify({"status": "ok", "rfid": last_rfid})


# ==================================================
# VIDEO STREAM API
# ==================================================
def gen_frames():
    global latest_frame

    while True:
        with camera_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ==================================================
# SENSOR STATUS API (Dashboard)
# ==================================================
@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": last_pir,
        "rfid": last_rfid,
        "pet_detected": pet_detected_flag,
        "behavior_score": behavior_score
    })


# ==================================================
# GET LOGS FOR DASHBOARD
# ==================================================
@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return jsonify([line.strip() for line in f.readlines()])


# ==================================================
# MAIN PAGE
# ==================================================
@app.route("/")
def index():
    return render_template("index.html")


# ==================================================
# START SERVER
# ==================================================
if __name__ == "__main__":
    print("🚀 PET SYSTEM STARTING...")
    init_camera()
    threading.Thread(target=camera_loop, daemon=True).start()
    app.run(debug=True, threaded=True, use_reloader=False)

from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
import os
from datetime import datetime
from ultralytics import YOLO
import random

# ==================================================
# FLASK APP
# ==================================================
app = Flask(__name__)
LOG_FILE = "motion_log.txt"

# ==================================================
# LOAD YOLO MODEL (COCO)
# ==================================================
PET_MODEL = YOLO("yolov8n.pt")  # dùng COCO model nhận cat/dog
PET_THRESHOLD = 0.25

# ==================================================
# GLOBAL SENSOR STATES
# ==================================================
last_pir = 0
last_rfid = None
pet_detected_flag = False
behavior_score = 0

# ==================================================
# CAMERA SYSTEM
# ==================================================
camera = None
latest_frame = None
camera_lock = threading.Lock()
last_gray = None


# ==================================================
# CAMERA INIT
# ==================================================
def init_camera():
    global camera

    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (0, "Default OpenCV")
    ]

    for backend, name in backends:
        try:
            cam = cv2.VideoCapture(0, backend) if backend != 0 else cv2.VideoCapture(0)
            if cam.isOpened():
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera = cam
                print(f"📷 Camera started using {name}")
                return
        except:
            pass

    print("❌ Không thể mở camera!")


# ==================================================
# LOGGING HELPERS
# ==================================================
def write_log(msg):
    line = f"{datetime.now().strftime('%H:%M:%S')} - {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print("📝 LOG:", line)


def log_motion():
    write_log("Chuyển động được ghi nhận (Camera)")


def log_pet(label, conf):
    write_log(f"Phát hiện thú cưng: {label} ({conf:.2f})")


def log_pir():
    write_log("PIR: phát hiện chuyển động (Mô phỏng)")


def log_rfid(tag):
    write_log(f"RFID: quét thẻ {tag} (Mô phỏng)")


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

        # ------------ Motion detection ------------ #
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        motion = False
        if last_gray is None:
            last_gray = gray
        else:
            diff = cv2.absdiff(last_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                if cv2.contourArea(c) > 800:
                    motion = True
                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

            last_gray = gray

        if motion:
            log_motion()
            behavior_score = min(100, behavior_score + 5)
        else:
            behavior_score = max(0, behavior_score - 1)

        # ------------ YOLO pet detection ------------ #
        pet_detected_flag = False
        pet_label = "Không thấy"
        pet_conf = 0.0

        try:
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
                        pet_label = label
                        pet_conf = conf
                        log_pet(label, conf)

                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,200,255), 2)
                        cv2.putText(frame, f"{label} {conf:.2f}",
                                    (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                    (0,255,255), 2)

        except Exception as e:
            print("❌ YOLO ERROR:", e)

        # ------------ OVERLAY TEXT ------------ #
        cv2.putText(frame, f"Pet: {pet_label} ({pet_conf:.2f})",
                    (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255,200,0), 2)

        # ------------ UPDATE STREAM ------------- #
        with camera_lock:
            latest_frame = frame.copy()

        time.sleep(0.03)


# ==================================================
# ARDUINO SIMULATION THREAD
# ==================================================
def arduino_simulation_loop():
    global last_pir, last_rfid, behavior_score

    while True:
        action = random.choice(["pir", "rfid", "none"])

        # -------- Simulate PIR -------- #
        if action == "pir":
            last_pir = random.choice([0, 1])
            if last_pir == 1:
                log_pir()
                behavior_score = min(100, behavior_score + 3)
            print("📡 PIR mô phỏng:", last_pir)

        # -------- Simulate RFID -------- #
        elif action == "rfid":
            last_rfid = random.choice(["PET001", "PET002", "CAT123", "DOG789"])
            log_rfid(last_rfid)
            print("🎯 RFID mô phỏng:", last_rfid)

        time.sleep(3)


# ==================================================
# STREAM VIDEO
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
# SENSOR STATUS API
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
# GET LOGS API
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

    # Camera detection thread
    threading.Thread(target=camera_loop, daemon=True).start()

    # Arduino simulation (PIR + RFID)
    threading.Thread(target=arduino_simulation_loop, daemon=True).start()

    app.run(debug=True, threaded=True, use_reloader=False)

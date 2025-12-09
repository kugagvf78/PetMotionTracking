from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
from datetime import datetime

# === IMPORT MODULES CỦA M ===
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDReader
from sensors.motion_ai import AIMotionDetector
from ai.pet_detector import PetDetector
from ai.behavior import BehaviorAnalyzer

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ===== CAMERA GLOBAL STATE =====
camera = None
latest_frame = None
lock = threading.Lock()
camera_thread = None
should_stop = False

# ==== LOAD SENSORS / AI ====
pir = PIRSensor()
rfid = RFIDReader()
ai_motion = AIMotionDetector()
pet_ai = PetDetector()
behavior_ai = BehaviorAnalyzer()

# ====== CAMERA INIT ======
def init_camera():
    global camera

    if camera is not None:
        try:
            camera.release()
        except:
            pass
        camera = None
        time.sleep(0.3)

    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (0, "Default")
    ]

    for backend, name in backends:
        print(f"🔍 Trying backend: {name}")

        try:
            cam = cv2.VideoCapture(0) if backend == 0 else cv2.VideoCapture(0, backend)

            if not cam.isOpened():
                print(f"❌ {name} failed.")
                continue

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cam.set(cv2.CAP_PROP_FPS, 30)

            # Flush first frames
            for _ in range(5):
                cam.read()
                time.sleep(0.1)

            ret, frame = cam.read()
            if not ret:
                cam.release()
                continue

            print(f"✅ Camera OK with {name}")
            camera = cam
            return True
        except:
            continue

    print("❌ No backend works!")
    return False


# ===== CAMERA LOOP =====
def camera_loop():
    global latest_frame, should_stop, camera

    print("📸 Camera Thread Running...")

    while not should_stop:
        if camera is None or not camera.isOpened():
            init_camera()
            time.sleep(1)
            continue

        ret, frame = camera.read()
        if not ret:
            time.sleep(0.05)
            continue

        # AI: PET DETECTION
        pet_found = pet_ai.detect(frame)

        # AI: BEHAVIOR SCORE
        behavior_score = behavior_ai.predict(frame)

        # AI: MOTION DETECTION
        motion = ai_motion.detect(frame)

        # PIR SENSOR
        pir_triggered = pir.read_motion()

        # RFID SENSOR
        rfid_tag = rfid.read_tag()

        # GHI LOG CHUYỂN ĐỘNG
        if motion or pir_triggered:
            log_motion()

        # Lưu frame
        with lock:
            latest_frame = frame.copy()

        time.sleep(0.03)


# ===== STREAM VIDEO =====
def gen_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            continue

        with lock:
            frame = latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


# ===== LOGGING =====
def log_motion():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} - Motion detected\n")


# ===== ROUTES =====
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r") as f:
        logs = [line.strip() for line in f.readlines()]
    return jsonify(logs[::-1])


@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}

    with open(LOG_FILE, "r") as f:
        for line in f:
            if " - " not in line:
                continue

            time_str = line.split(" - ")[0][:5]  # HH:MM
            stats[time_str] = stats.get(time_str, 0) + 1

    return jsonify([{"time": t, "count": stats[t]} for t in sorted(stats.keys())])


@app.route("/camera_status")
def camera_status():
    return jsonify({
        "active": camera is not None and camera.isOpened()
    })


@app.route("/sensor_status")
def sensor_status():

    pir_active = pir.read_motion()
    rfid_tag = rfid.read_tag()

    # AI detection
    pet_detected = False
    behavior_score = 0

    if latest_frame is not None:
        pet_detected = pet_ai.detect(latest_frame)
        behavior_score = behavior_ai.predict(latest_frame)

    return jsonify({
        "pir": pir_active,
        "rfid": rfid_tag,
        "pet_detected": pet_detected,
        "behavior_score": behavior_score
    })


# ===== START CAMERA THREAD =====
def start_camera():
    global camera_thread
    if camera_thread is None:
        camera_thread = threading.Thread(target=camera_loop, daemon=True)
        camera_thread.start()


if __name__ == "__main__":
    print("🚀 Starting Pet Tracking System...")
    start_camera()
    app.run(debug=True, threaded=True, use_reloader=False)

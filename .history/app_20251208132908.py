from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
import atexit
from datetime import datetime

# ===== IMPORT MODULES =====
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDReader
from ai.pet_detector import detect_pet
from ai.behavior import analyze_behavior

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ======== GLOBAL CAMERA VARS =========
camera = None
latest_frame = None
lock = threading.Lock()
camera_thread = None
should_stop = False

# ======== SENSOR STATES =========
pir = PIRSensor()
rfid = RFIDReader()

pir_triggered = False
last_rfid = None
last_pet_detect = False
behavior_score = 0


# ======== INIT CAMERA =========
def init_camera():
    global camera

    if camera is not None:
        try: camera.release()
        except: pass
        camera = None
        time.sleep(0.3)

    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (0, "Default"),
    ]

    for backend, name in backends:
        print(f"🔍 Thử backend: {name}")

        try:
            cam = cv2.VideoCapture(0, backend) if backend != 0 else cv2.VideoCapture(0)

            if not cam.isOpened():
                print(f"❌ Không mở được {name}")
                continue

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cam.set(cv2.CAP_PROP_FPS, 30)
            cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            ret, frame = cam.read()
            if not ret or frame is None:
                print(f"❌ {name}: mở nhưng không đọc được frame")
                cam.release()
                continue

            print(f"✅ Camera mở bằng {name}")
            camera = cam
            return True

        except Exception as e:
            print("⚠ Camera error:", e)

    print("❌ TẤT CẢ backend đều fail!")
    return False


# ========= CAMERA THREAD ==========
def camera_loop():
    global latest_frame, camera, should_stop
    global pir_triggered, last_rfid, last_pet_detect, behavior_score

    print("📹 Camera thread START")

    last_gray = None

    while not should_stop:
        if camera is None or not camera.isOpened():
            if not init_camera():
                time.sleep(1)
                continue

        camera.grab()
        ret, frame = camera.retrieve()

        if not ret or frame is None:
            time.sleep(0.05)
            continue

        # ============================
        # MOTION DETECTION
        # ============================
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_gray is not None:
            diff = cv2.absdiff(last_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in contours:
                if cv2.contourArea(c) > 800:
                    log_motion()
                    break

        last_gray = gray

        # ============================
        # AI PET DETECTION
        # ============================
        pet_found = detect_pet(frame)
        last_pet_detect = pet_found
        if pet_found:
            with open("static/alerts/pet.txt", "w") as f:
                f.write("Pet detected")
        else:
            try: os.remove("static/alerts/pet.txt")
            except: pass

        # ============================
        # AI BEHAVIOR SCORE
        # ============================
        behavior_score = analyze_behavior(frame)
        with open("static/alerts/behavior.txt", "w") as f:
            f.write(str(behavior_score))

        # ============================
        # UPDATE FRAME
        # ============================
        with lock:
            latest_frame = frame.copy()

        time.sleep(0.03)


# ========== PIR THREAD ==========
def pir_loop():
    global pir_triggered

    while True:
        state = pir.read()
        pir_triggered = state

        if state:
            with open("static/alerts/pir.txt", "w") as f:
                f.write("PIR triggered")
        else:
            try: os.remove("static/alerts/pir.txt")
            except: pass

        time.sleep(0.3)


# ========== RFID THREAD ==========
def rfid_loop():
    global last_rfid

    while True:
        tag = rfid.read()
        last_rfid = tag

        if tag:
            with open("static/alerts/rfid.txt", "w") as f:
                f.write(f"RFID: {tag}")
        else:
            try: os.remove("static/alerts/rfid.txt")
            except: pass

        time.sleep(0.5)


# ========== MOTION LOG ==========
def log_motion():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%H:%M:%S") + " - Motion detected\n")


# ========== STREAM ==========
def gen_frames():
    while True:
        with lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            frame = cv2.imread("static/no_camera.jpg")

        ret, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": pir_triggered,
        "rfid": last_rfid,
        "pet": last_pet_detect,
        "behavior": behavior_score
    })


# ========== STARTUP ==========
if __name__ == "__main__":
    print("🚀 Khởi động hệ thống...")

    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=pir_loop, daemon=True).start()
    threading.Thread(target=rfid_loop, daemon=True).start()

    app.run(debug=True, use_reloader=False)

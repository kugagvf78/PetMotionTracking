from flask import Flask, render_template, Response, jsonify
import cv2, time, threading, os, atexit

# ===== AI & Sensors =====
from ai.pet_detector import PetDetector
from ai.behavior import BehaviorAnalyzer
from sensors.motion_ai import MotionAIDetector
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDSensor

app = Flask(__name__)
LOG_FILE = "motion_log.txt"

# ==============================
# GLOBALS
# ==============================
camera = None
latest_frame = None
lock = threading.Lock()
should_stop = False

# Sensors + AI
pet_ai = PetDetector()
behavior_ai = BehaviorAnalyzer()
motion_ai = MotionAIDetector()
pir = PIRSensor()
rfid = RFIDSensor()


# ==============================
# LOG FUNCTION
# ==============================
def log_motion():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - Motion detected\n")


# ==============================
# INIT CAMERA
# ==============================
def init_camera():
    global camera

    if camera is not None:
        try: camera.release()
        except: pass
        camera = None
        time.sleep(0.2)

    # MSMF ổn định nhất trên Windows
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv2.CAP_PROP_FPS, 30)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cam.isOpened():
        print("❌ Camera không mở được!")
        return False

    print("✅ Camera đã mở thành công!")
    camera = cam
    return True


# ==============================
# CAMERA THREAD (HIGH FPS)
# ==============================
def camera_loop():
    global latest_frame, should_stop, camera

    print("🎥 Camera thread started...")

    while not should_stop:
        if camera is None or not camera.isOpened():
            init_camera()
            time.sleep(1)
            continue

        # Bỏ buffer cho mượt
        camera.grab()
        ret, frame = camera.retrieve()

        if not ret:
            time.sleep(0.01)
            continue

        # ==========================
        # MOTION AI
        # ==========================
        motion_level = motion_ai.detect(frame)
        if motion_level > 0:
            log_motion()

        # ==========================
        # PET AI
        # ==========================
        pet_label, pet_conf = pet_ai.detect(frame)

        # ==========================
        # Behavior AI
        # ==========================
        behavior_score = behavior_ai.update(motion_level)

        # ==========================
        # PIR + RFID
        # ==========================
        pir_state = pir.read_motion()
        rfid_tag = rfid.read_tag()

        # ==========================
        # OVERLAY TEXT
        # ==========================
        cv2.putText(frame, f"Motion: {motion_level}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.putText(frame, f"Pet: {pet_label} ({pet_conf:.2f})", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        cv2.putText(frame, f"Behavior Score: {behavior_score}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100,200,255), 2)

        cv2.putText(frame, f"PIR: {pir_state}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

        cv2.putText(frame, f"RFID: {rfid_tag}", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,150,255), 2)

        # ==========================
        # UPDATE FRAME
        # ==========================
        with lock:
            latest_frame = frame

        time.sleep(0.01)

    print("📷 Camera thread stopped.")


# ==============================
# MJPEG STREAM
# ==============================
def gen_frames():
    global latest_frame

    while True:
        with lock:
            frame = latest_frame

        if frame is None:
            continue

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")


# ==============================
# ROUTES
# ==============================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera_status")
def camera_status():
    return jsonify({
        "status": "active" if camera and camera.isOpened() else "inactive",
        "has_frame": latest_frame is not None
    })


@app.route("/pir")
def pir_api():
    return jsonify({"pir": pir.read_motion()})


@app.route("/rfid")
def rfid_api():
    return jsonify({"tag": rfid.read_tag()})


@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": pir.read_motion(),
        "rfid": rfid.read_tag()
    })


@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs[::-1])


@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            t = line.split(" - ")[0]
            minute = t[:5]
            stats[minute] = stats.get(minute, 0) + 1

    return jsonify([{"time": k, "count": v} for k, v in sorted(stats.items())])


# ==============================
# CLEAN EXIT
# ==============================
def cleanup():
    global should_stop
    should_stop = True
    if camera:
        camera.release()
    cv2.destroyAllWindows()

atexit.register(cleanup)


# ==============================
# START SYSTEM
# ==============================
if __name__ == "__main__":
    print("🚀 Starting system...")
    threading.Thread(target=camera_loop, daemon=True).start()
    app.run(debug=True, threaded=True, use_reloader=False)

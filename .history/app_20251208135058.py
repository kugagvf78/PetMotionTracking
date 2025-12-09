from flask import Flask, render_template, Response, jsonify
import cv2, time, threading, os, atexit

# ===== IMPORT AI & SENSORS =====
from ai.pet_detector import PetDetector
from ai.behavior import BehaviorAnalyzer
from sensors.motion_ai import MotionAIDetector
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDSensor

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ==============================
# GLOBAL OBJECTS
# ==============================
camera = None
latest_frame = None
lock = threading.Lock()
should_stop = False

# AI + Sensors
pet_ai = PetDetector()
behavior_ai = BehaviorAnalyzer()
motion_ai = MotionAIDetector()

pir = PIRSensor()
rfid = RFIDSensor()

motion_score = 0
last_pet = "None"
behavior_score = 0
pir_state = False
last_rfid = None

# ==============================
# CAMERA INIT
# ==============================
def init_camera():
    global camera

    # release if exists
    if camera is not None:
        try: camera.release()
        except: pass
        camera = None
        time.sleep(0.2)

    print("🎥 Initializing camera...")

    # MSMF = ổn định nhất trên Windows
    cam = cv2.VideoCapture(0, cv2.CAP_MSMF)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    cam.set(cv2.CAP_PROP_FPS, 30)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cam.isOpened():
        print("❌ Camera failed to open!")
        return False

    camera = cam
    print("✅ Camera ready!")
    return True


# ==============================
# CAMERA THREAD (FPS MAX)
# ==============================
def camera_loop():
    global latest_frame, camera, should_stop

    print("🎥 Camera thread started")

    if not init_camera():
        print("❌ No camera detected")
        return

    while not should_stop:
        if camera is None or not camera.isOpened():
            print("🔄 Reinitializing camera...")
            init_camera()
            time.sleep(0.3)
            continue

        # flush buffer → giảm lag
        camera.grab()
        ret, frame = camera.retrieve()

        if not ret:
            continue

        # store latest frame
        with lock:
            latest_frame = frame

        # ✨ remove big delay (FPS boost)
        time.sleep(0.005)

    print("❌ Camera loop stopped")


# ==============================
# AI THREAD (chạy song song)
# ==============================
def ai_loop():
    global motion_score, last_pet, behavior_score
    global pir_state, last_rfid, should_stop

    print("🤖 AI thread started")

    while not should_stop:

        if latest_frame is None:
            time.sleep(0.05)
            continue

        frame = None
        with lock:
            frame = latest_frame.copy()

        # Motion AI
        motion_score = motion_ai.detect(frame)

        # Pet AI
        last_pet = pet_ai.detect(frame)

        # Behavior scoring
        behavior_score = behavior_ai.update(motion_score)

        # PIR
        pir_state = pir.read()

        # RFID
        last_rfid = rfid.read_tag()

        # GIẢM tải CPU → ổn định
        time.sleep(0.05)

    print("❌ AI loop stopped")


# ==============================
# STREAM MJPEG
# ==============================
def gen_frames():
    while True:
        frame = None
        with lock:
            frame = latest_frame

        if frame is None:
            continue

        # JPEG compress (70 quality = ít lag)
        ret, buffer = cv2.imencode(".jpg", frame, 
                                   [cv2.IMWRITE_JPEG_QUALITY, 70])

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
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
        "status": "active" if (camera and camera.isOpened()) else "inactive",
        "has_frame": latest_frame is not None
    })


@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": pir_state,
        "rfid": last_rfid,
        "motion": motion_score,
        "pet": last_pet,
        "behavior": behavior_score
    })


@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}
    with open(LOG_FILE, "r") as f:
        for line in f:
            t = line.split(" - ")[0]
            minute = t[:5]
            stats[minute] = stats.get(minute, 0) + 1

    return jsonify([{"time": k, "count": v} for k, v in sorted(stats.items())])


@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs[::-1])  # newest first


# ==============================
# CLEANUP
# ==============================
def cleanup():
    global should_stop
    should_stop = True
    try:
        if camera: camera.release()
    except:
        pass

atexit.register(cleanup)


# ==============================
# START SYSTEM
# ==============================
if __name__ == "__main__":
    print("🚀 Starting system...")

    # Camera thread
    threading.Thread(target=camera_loop, daemon=True).start()

    # AI thread
    threading.Thread(target=ai_loop, daemon=True).start()

    # Flask
    app.run(debug=True, threaded=True, use_reloader=False)

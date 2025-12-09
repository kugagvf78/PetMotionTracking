from flask import Flask, render_template, Response, jsonify
import cv2, time, threading, os, atexit

# ===== IMPORT MODULES =====
from ai.pet_detector import PetDetector
from ai.behavior import BehaviorAnalyzer
from sensors.motion_ai import MotionAIDetector
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDSensor

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ===== GLOBAL STATE =====
camera = None
latest_frame = None
lock = threading.Lock()

should_stop = False

# ===== INIT SENSORS =====
pet_ai = PetDetector()
behavior_ai = BehaviorAnalyzer()
motion_ai = MotionAIDetector()
pir = PIRSensor()
rfid = RFIDSensor()

# ======================================================
# CAMERA INIT — include buffer fix to reduce lag
# ======================================================
def init_camera():
    global camera

    if camera is not None:
        try:
            camera.release()
        except:
            pass
        camera = None
        time.sleep(0.2)

    # Use MSMF backend (best for Windows 10+)
    camera = cv2.VideoCapture(0, cv2.CAP_MSMF)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    return camera.isOpened()

# ======================================================
# LOG MOTION EVENTS
# ======================================================
def log_motion():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - Motion detected\n")

# ======================================================
# CAMERA THREAD LOOP
# ======================================================
def camera_loop():
    global latest_frame, camera, should_stop

    while not should_stop:

        if camera is None or not camera.isOpened():
            init_camera()
            time.sleep(0.3)
            continue

        # ⚡ Lấy frame nhanh — flush buffer giảm lag
        camera.grab()
        ret, frame = camera.retrieve()

        if not ret:
            continue

        # ⚡ Không chạy AI trong camera thread nữa → giữ FPS cao
        with lock:
            latest_frame = frame

        # ⚡ Giảm delay → tăng FPS
        # time.sleep(0.03)  # REMOVE THIS
        time.sleep(0.005)  # ~200 FPS theoretical, ~30FPS real


def ai_loop():
    global latest_frame, should_stop

    while not should_stop:
        if latest_frame is None:
            time.sleep(0.05)
            continue

        frame_copy = latest_frame.copy()

        # Chạy AI ở thread riêng → không ảnh hưởng camera FPS
        motion_val = motion_ai.detect(frame_copy)
        pet_seen = pet_ai.detect(frame_copy)
        behavior_ai.update(motion_val)

        # PIR + RFID
        pir.read_motion()
        rfid.read_tag()

        time.sleep(0.05)
# ======================================================
# STREAM MJPEG TO BROWSER
# ======================================================
def gen_frames():
    global latest_frame

    while True:
        with lock:
            frame = latest_frame

        if frame is None:
            continue

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               frame_bytes +
               b"\r\n")

# ======================================================
# ROUTES
# ======================================================
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

@app.route("/pir")
def pir_api():
    return jsonify({"pir": pir.read_motion()})

@app.route("/rfid")
def rfid_api():
    return jsonify({"tag": rfid.last_tag})

@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": pir.read_motion(),
        "rfid": rfid.last_tag
    })

@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}
    with open(LOG_FILE, "r") as f:
        for line in f:
            if " - " not in line:
                continue
            t = line.split(" - ")[0]
            minute = t[:5]
            stats[minute] = stats.get(minute, 0) + 1

    result = [{"time": k, "count": v} for k, v in sorted(stats.items())]
    return jsonify(result)

@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(list(reversed(logs)))

# ======================================================
# CLEANUP ON EXIT
# ======================================================
def cleanup():
    global should_stop, camera
    should_stop = True
    if camera is not None:
        camera.release()
    cv2.destroyAllWindows()

atexit.register(cleanup)

# ======================================================
# START SYSTEM
# ======================================================
if __name__ == "__main__":
    print("🚀 Starting Pet Tracking System...")
    threading.Thread(target=camera_loop, daemon=True).start()
    app.run(debug=True, threaded=True, use_reloader=False)

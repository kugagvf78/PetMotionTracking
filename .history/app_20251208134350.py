from flask import Flask, render_template, Response, jsonify
import cv2, time, threading, os, atexit

from ai.pet_detector import PetDetector        # ✔ file bạn có
from ai.behavior import BehaviorAnalyzer       # ✔ file bạn có
from sensors.motion_ai import MotionAIDetector # ✔ tên class mình chuẩn hóa lại
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDSensor

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ========================
# GLOBAL MODULES
# ========================
camera = None
latest_frame = None
lock = threading.Lock()

pet_ai = PetDetector()
behavior_ai = BehaviorAnalyzer()
motion_ai = MotionAIDetector()
pir = PIRSensor()
rfid = RFIDSensor()

should_stop = False

# ========================
# INIT CAMERA
# ========================
def init_camera():
    global camera
    if camera is not None:
        try:
            camera.release()
        except:
            pass
        camera = None
        time.sleep(0.3)

    camera = cv2.VideoCapture(0, cv2.CAP_MSMF)
    camera.set(3, 640)
    camera.set(4, 480)
    return camera.isOpened()

# ========================
# MOTION LOGGING
# ========================
def log_motion():
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - Motion detected\n")

# ========================
# CAMERA THREAD
# ========================
def camera_loop():
    global latest_frame, camera, should_stop

    while not should_stop:
        if camera is None or not camera.isOpened():
            init_camera()
            time.sleep(1)
            continue

        ret, frame = camera.read()
        if not ret:
            time.sleep(0.05)
            continue

        # ====== AI Motion Detection ======
        motion_level = motion_ai.detect(frame)

        if motion_level > 0:
            log_motion()

        # ====== Pet Detection ======
        pet_seen = pet_ai.detect(frame)

        # ====== Behavior Analysis ======
        behavior_info = behavior_ai.update(motion_level)

        # ====== PIR + RFID ======
        pir_state = pir.read()
        rfid_id = rfid.read_tag()

        # Overlay data for debug
        cv2.putText(frame, f"Motion: {motion_level}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(frame, f"Pet: {pet_seen}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

        with lock:
            latest_frame = frame

        time.sleep(0.03)

    print("Camera thread stopped.")


# ========================
# STREAM MJPEG
# ========================
def gen_frames():
    while True:
        with lock:
            frame = latest_frame

        if frame is None:
            continue
        
        ret, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")

# ========================
# ROUTES
# ========================
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
    return jsonify({"pir": pir.read()})

@app.route("/rfid")
def rfid_api():
    return jsonify({"tag": rfid.read_tag()})


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

@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": pir.read_motion() if pir else False,
        "rfid": rfid.last_tag if rfid else None
    })
    
    @app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs[::-1])  # newest first

# ========================
# STARTUP
# ========================
def cleanup():
    global should_stop
    should_stop = True
    if camera:
        camera.release()

atexit.register(cleanup)

if __name__ == "__main__":
    print("🚀 Starting system...")
    threading.Thread(target=camera_loop, daemon=True).start()
    app.run(debug=True, threaded=True, use_reloader=False)

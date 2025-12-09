from flask import Flask, render_template, Response, jsonify
import cv2, time, threading, os, atexit

# ======= IMPORT MODULES =======
from ai.pet_detector import PetDetector
from ai.behavior import BehaviorAnalyzer

from sensors.motion_ai import MotionAIDetector
from sensors.pir_sensor import PIRSensor
from sensors.rfid_sensor import RFIDSensor

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ======= GLOBALS =======
camera = None
latest_frame = None
lock = threading.Lock()
should_stop = False

# AI Modules
motion_ai = MotionAIDetector()
pet_ai = PetDetector()
behavior_ai = BehaviorAnalyzer()

# Sensors
pir = PIRSensor()
rfid = RFIDSensor()

# ============================================================
# INIT CAMERA
# ============================================================
def init_camera():
    global camera
    try:
        if camera is not None:
            camera.release()
    except:
        pass

    # MSMF backend tối ưu cho Win10/11
    camera = cv2.VideoCapture(0, cv2.CAP_MSMF)

    # Camera settings
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    return camera.isOpened()

# ============================================================
# LOGGING
# ============================================================
def log_motion():
    """Ghi lại sự kiện chuyển động vào file"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - Motion detected\n")


# ============================================================
# CAMERA THREAD – đọc camera + AI + overlay
# ============================================================
def camera_loop():
    global latest_frame, should_stop, camera

    print("📸 Camera thread started.")

    while not should_stop:
        if camera is None or not camera.isOpened():
            print("🔄 Reinitializing camera...")
            init_camera()
            time.sleep(0.5)
            continue

        # Flush old buffers (giảm lag)
        camera.grab()
        ret, frame = camera.retrieve()

        if not ret or frame is None:
            time.sleep(0.02)
            continue

        # ---- Motion Detection ----
        motion_score = motion_ai.detect(frame)

        if motion_score > 2500:  # Ngưỡng tuỳ chỉnh
            log_motion()

        # ---- Pet Detection ----
        pet_label, pet_conf = pet_ai.detect(frame)

        # ---- Behavior Analyzer ----
        behavior_score = behavior_ai.update(motion_score)

        # ---- PIR/RFID ----
        pir_state = pir.read()
        rfid_tag = rfid.read()

        # ---- Overlay thông tin ----
        cv2.putText(frame, f"Motion: {motion_score}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0), 2)

        cv2.putText(frame, f"Pet: {pet_label} ({pet_conf:.2f})",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 255), 2)

        cv2.putText(frame, f"Behavior: {behavior_score}",
                    (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 100, 0), 2)

        cv2.putText(frame, f"PIR: {pir_state}",
                    (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (200, 200, 200), 2)

        cv2.putText(frame, f"RFID: {rfid_tag}",
                    (10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 150, 255), 2)

        # ---- Update frame ----
        with lock:
            latest_frame = frame.copy()

        time.sleep(0.02)

    print("❌ Camera loop stopped")


# ============================================================
# STREAM MJPEG
# ============================================================
def gen_frames():
    while True:
        with lock:
            frame = latest_frame

        if frame is None:
            continue

        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


# ============================================================
# FLASK ROUTES
# ============================================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera_status")
def camera_status():
    return jsonify({
        "active": camera.isOpened() if camera else False,
        "has_frame": latest_frame is not None
    })


@app.route("/motion_stats")
def motion_stats():
    """Return motion count per minute"""
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

    data = [{"time": k, "count": v} for k, v in sorted(stats.items())]
    return jsonify(data)


@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r") as f:
        logs = [line.strip() for line in f.readlines()]

    return jsonify(logs[::-1])


@app.route("/sensor_status")
def sensor_status():
    return jsonify({
        "pir": pir.read(),
        "rfid": rfid.read(),
    })


# ============================================================
# CLEANUP
# ============================================================
def cleanup():
    global should_stop
    should_stop = True
    if camera:
        camera.release()
    print("🧹 Cleanup done.")

atexit.register(cleanup)


# ============================================================
# MAIN START
# ============================================================
if __name__ == "__main__":
    print("🚀 SYSTEM STARTING...")

    # Start camera thread
    threading.Thread(target=camera_loop, daemon=True).start()

    # Start Flask
    app.run(debug=True, threaded=True, use_reloader=False)

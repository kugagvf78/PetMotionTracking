from flask import Flask, render_template, Response, jsonify
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
print("🔍 Loading YOLO COCO model...")
PET_MODEL = YOLO("yolov8n.pt")   # đổi thành yolov8s.pt nếu muốn mạnh hơn
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


def init_camera():
    """Thử mở camera bằng nhiều backend."""
    global camera

    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (0, "Default OpenCV")
    ]

    for backend, name in backends:
        print(f"🔍 Thử mở camera với backend: {name}")
        try:
            cam = cv2.VideoCapture(0, backend) if backend != 0 else cv2.VideoCapture(0)

            if cam.isOpened():
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cam.set(cv2.CAP_PROP_FPS, 20)
                cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                ret, frame = cam.read()
                if ret:
                    print(f"✅ Camera mở thành công bằng {name}")
                    camera = cam
                    return True

                cam.release()

        except Exception as e:
            print("❌ Camera error:", e)

    print("⚠ Không thể mở camera!")
    return False


def camera_loop():
    """Luồng xử lý camera chính."""
    global latest_frame, last_gray
    global pet_detected_flag, behavior_score

    error_count = 0

    while True:
        try:
            if camera is None or not camera.isOpened():
                print("🔄 Đang thử mở lại camera...")
                init_camera()
                time.sleep(1)
                continue

            ret, frame = camera.read()
            if not ret:
                error_count += 1
                print(f"⚠ Lỗi đọc frame ({error_count}/10)")
                if error_count >= 10:
                    camera.release()
                    camera = None
                continue

            error_count = 0

            # ==================================================
            # MOTION DETECTION
            # ==================================================
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            motion_detected = False

            if last_gray is None:
                last_gray = gray
            else:
                diff = cv2.absdiff(last_gray, gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for c in contours:
                    if cv2.contourArea(c) > 800:
                        motion_detected = True
                        x, y, w, h = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                last_gray = gray

            if motion_detected:
                log_motion()
                behavior_score = min(100, behavior_score + 5)
            else:
                behavior_score = max(0, behavior_score - 1)

            # ==================================================
            # YOLO PET DETECTION — COCO MODEL
            # ==================================================
            pet_label = "Không thấy"
            pet_conf = 0.00
            pet_detected_flag = False

            try:
                results = PET_MODEL.predict(frame, conf=PET_THRESHOLD, verbose=False)

                for r in results:
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        label = PET_MODEL.names[cls]

                        if label not in ["dog", "cat"]:
                            continue

                        print("🐶 YOLO DETECT:", label, conf)

                        if conf >= PET_THRESHOLD:
                            pet_label = label
                            pet_conf = conf
                            pet_detected_flag = True

                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
                            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 5),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            except Exception as e:
                print("🔥 YOLO Error:", e)

            # Overlay text
            cv2.putText(frame, f"Pet: {pet_label} ({pet_conf:.2f})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

            # ==================================================
            # UPDATE STREAM FRAME
            # ==================================================
            with camera_lock:
                latest_frame = frame.copy()

        except Exception as e:
            print("❌ Camera loop error:", e)

        time.sleep(0.03)


# ==================================================
# LOGGING SYSTEM
# ==================================================
last_log_time = 0
LOG_COOLDOWN = 2


def log_motion():
    global last_log_time

    now = time.time()
    if now - last_log_time < LOG_COOLDOWN:
        return
    last_log_time = now

    msg = f"{datetime.now().strftime('%H:%M:%S')} - Chuyển động được ghi nhận!"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

    print("📌 LOG:", msg)


# ==================================================
# API: STREAM VIDEO
# ==================================================
def gen_frames():
    global latest_frame
    while True:
        with camera_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")


# ==================================================
# API: SENSOR STATUS (Dashboard cần API này)
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
# API: CAMERA STATUS
# ==================================================
@app.route("/camera_status")
def camera_status():
    return jsonify({
        "active": camera is not None and camera.isOpened(),
        "has_frame": latest_frame is not None
    })


# ==================================================
# API: MOTION STATS
# ==================================================
@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if " - " in line:
                key = line.split(" - ")[0][:5]
                stats[key] = stats.get(key, 0) + 1

    return jsonify([{"time": k, "count": v} for k, v in sorted(stats.items())])


# ==================================================
# DASHBOARD
# ==================================================
@app.route("/")
def index():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [line.strip() for line in f.readlines()]
    return render_template("index.html", logs=logs)


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ==================================================
# START SERVER
# ==================================================
if __name__ == "__main__":
    print("🚀 PET MONITOR STARTING...")
    init_camera()
    threading.Thread(target=camera_loop, daemon=True).start()
    app.run(debug=True, threaded=True, use_reloader=False)

from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
import atexit
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ========= GLOBAL CAMERA STATE ==========
camera = None
latest_frame = None
lock = threading.Lock()
camera_thread = None
should_stop = False

# ========= MOTION DETECTION GLOBAL ==========
last_gray = None
LOG_COOLDOWN = 2
last_log_time = 0


# ========= GHI LOG ==========
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


# ========= INIT CAMERA ==========
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
        print(f"🔍 Thử mở camera với backend: {name}")

        try:
            cam = cv2.VideoCapture(0, backend) if backend != 0 else cv2.VideoCapture(0)

            if not cam.isOpened():
                print(f"❌ Không mở được camera bằng {name}")
                continue

            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cam.set(cv2.CAP_PROP_FPS, 30)
            cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # đọc 5 frame đầu để ổn định camera
            for _ in range(5):
                cam.read()
                time.sleep(0.1)

            ret, frame = cam.read()
            if not ret or frame is None:
                print(f"⚠ Camera mở nhưng không đọc được frame")
                cam.release()
                continue

            print(f"✅ Camera hoạt động tốt với {name}")
            camera = cam
            return True

        except Exception as e:
            print(f"❌ Lỗi backend {name}: {e}")
            continue

    print("❌ Không thể khởi tạo camera!")
    return False


# ========= CAMERA THREAD ==========
def camera_loop():
    global latest_frame, camera, should_stop, last_gray

    print("📹 Camera thread STARTED")

    error_count = 0
    frame_count = 0

    while not should_stop:
        try:
            if camera is None or not camera.isOpened():
                print("🔄 Camera chưa sẵn sàng → khởi tạo lại...")
                if not init_camera():
                    time.sleep(2)
                    continue

            camera.grab()
            ret, frame = camera.retrieve()

            if not ret or frame is None:
                error_count += 1
                print(f"⚠ Lỗi đọc frame ({error_count}/10)")

                if error_count >= 10:
                    print("❌ Camera lỗi nặng → reset lại")
                    camera.release()
                    camera = None
                    error_count = 0

                time.sleep(0.1)
                continue

            error_count = 0
            frame_count += 1

            # ========== MOTION DETECTION ==========
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if last_gray is None:
                last_gray = gray
            else:
                diff = cv2.absdiff(last_gray, gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                contours, _ = cv2.findContours(
                    thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                motion_found = False
                for c in contours:
                    if cv2.contourArea(c) < 900:  # lọc nhiễu
                        continue

                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x+w, y+h),
                                  (0, 255, 0), 2)

                    if not motion_found:
                        log_motion()
                        motion_found = True

                last_gray = gray

            with lock:
                latest_frame = frame.copy()

            time.sleep(0.03)

        except Exception as e:
            print("❌ camera_loop error:", e)
            time.sleep(0.3)

    print("📹 Camera thread STOPPED")


# ========= START CAMERA THREAD ==========
def start_camera_thread():
    global camera_thread
    if camera_thread is None or not camera_thread.is_alive():
        print("🚀 Khởi động camera...")
        if init_camera():
            camera_thread = threading.Thread(
                target=camera_loop, daemon=True)
            camera_thread.start()
        else:
            print("❌ Không thể khởi động camera!")


# ========= STREAM ==========
def gen_frames():
    global latest_frame

    while True:
        with lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            frame = cv2.UMat((480, 640, 3)).get()
            cv2.putText(frame, "Camera dang khoi dong...",
                        (120, 240), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 255, 255), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               frame_bytes + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ========= ROUTES ==========
@app.route("/")
def index():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [line.strip() for line in f]

    return render_template("index.html", logs=logs)


@app.route("/camera_status")
def camera_status():
    return jsonify({
        "status": "active" if (camera and camera.isOpened()) else "inactive",
        "has_frame": latest_frame is not None
    })


@app.route("/get_logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = [line.strip() for line in f if line.strip()]

    return jsonify(logs[::-1])


@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if " - " not in line:
                continue

            time_key = line.split(" - ")[0][:5]  # HH:MM
            stats[time_key] = stats.get(time_key, 0) + 1

    result = [{"time": k, "count": stats[k]} for k in sorted(stats.keys())]
    return jsonify(result)


# ========= CLEANUP ==========
def cleanup():
    global should_stop, camera
    should_stop = True
    if camera:
        camera.release()
    cv2.destroyAllWindows()


atexit.register(cleanup)


# ========= START ==========
if __name__ == "__main__":
    print("🚀 PET MOTION TRACKING SYSTEM RUNNING...")
    start_camera_thread()
    app.run(debug=True, threaded=True, use_reloader=False)

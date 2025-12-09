from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ========= CAMERA GLOBAL ==========
camera = None
latest_frame = None
lock = threading.Lock()


# ========= INIT CAMERA PROPERLY =============
def init_camera():
    global camera

    # luôn reset camera về None
    if camera is not None:
        camera.release()
        camera = None
        time.sleep(0.2)

    backends = [
        (cv2.CAP_MSMF, "MSMF"),
        (cv2.CAP_DSHOW, "DSHOW"),
        (0, "DEFAULT"),
    ]

    for backend, name in backends:
        print(f"🔍 Thử mở camera bằng backend {name}...")

        if backend == 0:
            cam = cv2.VideoCapture(0)
        else:
            cam = cv2.VideoCapture(0, backend)

        if not cam.isOpened():
            print(f"❌ Không mở được camera với {name}")
            continue

        # Set cấu hình
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # test frame
        ret, frame = cam.read()
        if not ret or frame is None:
            print(f"❌ Camera mở bằng {name} nhưng không đọc được frame!")
            cam.release()
            continue

        print(f"✅ Camera OK với backend {name}")
        camera = cam
        return True

    print("❌ TẤT CẢ backend đều thất bại — camera không hoạt động!")
    return False


# ========== CAMERA THREAD =================
def camera_loop():
    global latest_frame, camera

    while True:
        if camera is None or not camera.isOpened():
            print("🔄 Camera không mở — đang thử lại...")
            init_camera()
            time.sleep(1)
            continue

        # flush buffer
        camera.read()
        ret, frame = camera.read()

        if not ret or frame is None:
            print("⚠ Frame lỗi — reset camera")
            init_camera()
            continue

        with lock:
            latest_frame = frame.copy()

        time.sleep(0.03)


# Start camera thread
threading.Thread(target=camera_loop, daemon=True).start()


# ========== STREAMING MJPEG =============
def gen_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            time.sleep(0.05)
            continue

        with lock:
            frame = latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               frame_bytes + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    logs = []
    if os.path.exists(LOG_FILE):
        logs = open(LOG_FILE, "r", encoding="utf-8").read().splitlines()
    return render_template("index.html", logs=logs)


@app.route("/camera_status")
def camera_status():
    return jsonify({
        "opened": camera.isOpened() if camera else False,
        "has_frame": latest_frame is not None
    })


if __name__ == "__main__":
    print("🚀 Server chạy tại http://127.0.0.1:5000")
    app.run(debug=True, threaded=True)

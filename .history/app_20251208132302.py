from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
import atexit

app = Flask(__name__)

LOG_FILE = "motion_log.txt"

# ========= CAMERA GLOBAL ==========
camera = None
latest_frame = None
lock = threading.Lock()
camera_thread = None
should_stop = False


# ========= INIT CAMERA PROPERLY =============
def init_camera():
    global camera

    # Release existing camera
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
        (0, "Default"),
    ]

    for backend, name in backends:
        print(f"🔍 Thử mở camera với backend: {name}")

        try:
            if backend == 0:
                cam = cv2.VideoCapture(0)
            else:
                cam = cv2.VideoCapture(0, backend)

            if not cam.isOpened():
                print(f"❌ Không mở được với {name}")
                continue

            # Đặt cấu hình camera
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cam.set(cv2.CAP_PROP_FPS, 30)
            cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # QUAN TRỌNG: Đọc và bỏ qua vài frame đầu
            for i in range(5):
                ret, frame = cam.read()
                if ret and frame is not None:
                    print(f"   Frame {i+1}/5: OK ({frame.shape})")
                time.sleep(0.1)

            # Test frame cuối
            ret, frame = cam.read()
            if not ret or frame is None:
                print(f"❌ {name}: Camera mở nhưng không đọc được frame!")
                cam.release()
                continue

            print(f"✅ Camera hoạt động với {name}!")
            print(f"   Resolution: {int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            camera = cam
            return True

        except Exception as e:
            print(f"❌ Lỗi khi thử {name}: {e}")
            continue

    print("❌ Không thể mở camera với bất kỳ backend nào!")
    return False


# ========== CAMERA THREAD =================
def camera_loop():
    global latest_frame, camera, should_stop
    
    error_count = 0
    frame_count = 0
    
    print("📹 Camera thread bắt đầu...")

    while not should_stop:
        try:
            # Kiểm tra camera
            if camera is None or not camera.isOpened():
                print("🔄 Camera chưa sẵn sàng, đang khởi tạo...")
                if not init_camera():
                    time.sleep(2)
                    continue
                error_count = 0

            # Đọc frame - flush buffer trước
            camera.grab()  # Bỏ frame cũ trong buffer
            ret, frame = camera.retrieve()

            if not ret or frame is None:
                error_count += 1
                print(f"⚠️ Lỗi đọc frame ({error_count}/10)")
                
                if error_count >= 10:
                    print("❌ Quá nhiều lỗi, reset camera...")
                    if camera:
                        camera.release()
                    camera = None
                    error_count = 0
                    time.sleep(1)
                    continue
                
                time.sleep(0.1)
                continue

            # Frame OK
            error_count = 0
            frame_count += 1
            
            # Debug mỗi 100 frames
            if frame_count % 100 == 0:
                print(f"📹 Camera OK - Frame #{frame_count}")

            with lock:
                latest_frame = frame.copy()

            time.sleep(0.03)  # ~30 FPS

        except Exception as e:
            print(f"❌ Lỗi trong camera_loop: {e}")
            error_count += 1
            time.sleep(0.5)

    print("📹 Camera thread đã dừng")


# ========== CLEANUP ON EXIT =============
def cleanup_camera():
    global camera, should_stop
    print("🧹 Đang dọn dẹp camera...")
    should_stop = True
    if camera is not None:
        camera.release()
        camera = None
    cv2.destroyAllWindows()

atexit.register(cleanup_camera)


# ========== START CAMERA (CHỈ 1 LẦN) =============
def start_camera_thread():
    global camera_thread
    
    # Chỉ start nếu chưa có thread
    if camera_thread is None or not camera_thread.is_alive():
        print("🚀 Khởi động camera thread...")
        if init_camera():
            camera_thread = threading.Thread(target=camera_loop, daemon=True)
            camera_thread.start()
        else:
            print("⚠️ Camera không khả dụng!")


# ========== STREAMING MJPEG =============
def gen_frames():
    global latest_frame

    while True:
        with lock:
            if latest_frame is None:
                # Tạo frame placeholder khi chưa có camera
                placeholder = cv2.imread('static/no_camera.jpg')
                if placeholder is None:
                    # Tạo frame đen với text
                    placeholder = cv2.UMat((480, 640, 3)).get()
                    cv2.putText(placeholder, "Camera dang khoi dong...", 
                               (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 
                               1, (255, 255, 255), 2)
                frame = placeholder
            else:
                frame = latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            time.sleep(0.05)
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [line.strip() for line in f if line.strip()]
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
        return jsonify(logs[::-1])  # Đảo ngược để mới nhất lên đầu


@app.route("/motion_stats")
def motion_stats():
    if not os.path.exists(LOG_FILE):
        return jsonify([])

    stats = {}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if " - " not in line:
                continue
            try:
                time_part = line.split(" - ")[0].strip().split(" ")[-1]
                minute = time_part[:5]  # "HH:MM"
                stats[minute] = stats.get(minute, 0) + 1
            except:
                continue

    result = [{"time": t, "count": stats[t]} for t in sorted(stats.keys())]
    return jsonify(result)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 PET MOTION TRACKING SYSTEM")
    print("=" * 60)
    print("📡 Server: http://127.0.0.1:5000")
    print("📹 Video: http://127.0.0.1:5000/video_feed")
    print("🔍 Status: http://127.0.0.1:5000/camera_status")
    print("=" * 60)
    
    # Start camera TRƯỚC KHI chạy Flask
    start_camera_thread()
    
    # QUAN TRỌNG: use_reloader=False để tránh Flask chạy 2 lần
    app.run(debug=True, threaded=True, use_reloader=False, host='0.0.0.0', port=5000)
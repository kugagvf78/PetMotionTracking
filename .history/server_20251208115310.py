    from flask import Flask, render_template, Response, jsonify, request
    import cv2
    import threading
    import time
    import os
    from datetime import datetime
    from arduino_sim import ArduinoSimulator

    app = Flask(__name__)
    arduino = ArduinoSimulator()

    LOG_FILE = "motion_log.txt"

    # ================================
    # CAMERA THREAD - FIX VERSION
    # ================================
    camera = None
    latest_frame = None
    last_gray = None
    camera_lock = threading.Lock()

    def init_camera():
        """Khởi tạo camera với nhiều cách thử"""
        global camera
        
        # Thử các backend khác nhau
        backends = [
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_MSMF, "Media Foundation"),
            (0, "Default")
        ]
        
        for backend, name in backends:
            print(f"🔍 Thử mở camera với backend: {name}")
            try:
                cam = cv2.VideoCapture(0, backend) if backend != 0 else cv2.VideoCapture(0)
                
                if cam.isOpened():
                    # Đặt FPS và resolution thấp hơn để ổn định
                    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cam.set(cv2.CAP_PROP_FPS, 20)
                    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # Test đọc frame
                    ret, test_frame = cam.read()
                    if ret and test_frame is not None:
                        print(f"✅ Camera mở thành công với {name}!")
                        print(f"   Resolution: {int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
                        camera = cam
                        return True
                    else:
                        print(f"❌ Không đọc được frame từ {name}")
                        cam.release()
                else:
                    print(f"❌ Không mở được camera với {name}")
            except Exception as e:
                print(f"❌ Lỗi khi thử {name}: {e}")
        
        print("⚠️ KHÔNG THỂ MỞ CAMERA!")
        return False

    def camera_loop():
        global latest_frame, last_gray, camera
        
        frame_count = 0
        error_count = 0
        max_errors = 10
        
        while True:
            try:
                if camera is None or not camera.isOpened():
                    print("🔄 Đang thử khởi tạo lại camera...")
                    if not init_camera():
                        time.sleep(2)
                        continue
                
                # Đọc frame
                ret, frame = camera.read()
                
                if not ret or frame is None:
                    error_count += 1
                    print(f"⚠️ Lỗi đọc frame ({error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        print("❌ Quá nhiều lỗi, reset camera...")
                        if camera:
                            camera.release()
                        camera = None
                        error_count = 0
                        time.sleep(1)
                        continue
                    
                    time.sleep(0.1)
                    continue
                
                # Reset error count khi đọc thành công
                error_count = 0
                frame_count += 1
                
                # Debug mỗi 100 frames
                if frame_count % 100 == 0:
                    print(f"📹 Camera OK - Frame #{frame_count}")
                
                # =========================
                # Motion Detection
                # =========================
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if last_gray is None:
                    last_gray = gray
                else:
                    diff = cv2.absdiff(last_gray, gray)
                    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                    thresh = cv2.dilate(thresh, None, iterations=2)

                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    motion_detected = False
                    for c in contours:
                        if cv2.contourArea(c) < 800:
                            continue
                        (x, y, w, h) = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        if not motion_detected:  # Log chỉ 1 lần
                            log_motion()
                            motion_detected = True

                    last_gray = gray

                # Cập nhật frame
                with camera_lock:
                    latest_frame = frame.copy()
                
                time.sleep(0.03)
                
            except Exception as e:
                print(f"❌ Lỗi trong camera_loop: {e}")
                error_count += 1
                time.sleep(0.5)


    # BẮT ĐẦU camera thread
    print("🚀 Đang khởi động camera...")
    if init_camera():
        t = threading.Thread(target=camera_loop, daemon=True)
        t.start()
    else:
        print("⚠️ WARNING: Camera không khả dụng!")

    # ================================
    # LOG FUNCTION
    # ================================
    last_log_time = 0
    LOG_COOLDOWN = 2  # giây

    def log_motion():
        global last_log_time
        
        current_time = time.time()
        if current_time - last_log_time < LOG_COOLDOWN:
            return
        
        last_log_time = current_time
        
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, "w", encoding="utf-8").close()

        msg = f"{datetime.now().strftime('%H:%M:%S')} - Chuyển động được ghi nhận!"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

        print("📌 LOG:", msg)


    # ================================
    # STREAM VIDEO
    # ================================
    def gen_frames():
        global latest_frame
        while True:
            with camera_lock:
                if latest_frame is None:
                    # Tạo frame đen với text
                    blank = cv2.imread('static/no_camera.jpg') if os.path.exists('static/no_camera.jpg') else \
                            cv2.putText(
                                cv2.rectangle(cv2.UMat((480, 640, 3)).get(), (0,0), (640,480), (20,20,20), -1),
                                "Camera dang khoi dong...", (150, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2
                            )
                    frame = blank
                else:
                    frame = latest_frame.copy()

            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


    @app.route("/")
    def index():
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = [line.strip() for line in f if line.strip()]
        return render_template("index.html", logs=logs)


    @app.route("/video_feed")
    def video_feed():
        return Response(gen_frames(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")


    @app.route("/get_logs")
    def get_logs():
        if not os.path.exists(LOG_FILE):
            return jsonify([])
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [line.strip() for line in f if line.strip()]
            return jsonify(logs[::-1])  # Đảo ngược để log mới nhất lên đầu


    @app.route("/camera_status")
    def camera_status():
        """Endpoint kiểm tra trạng thái camera"""
        return jsonify({
            "status": "active" if camera and camera.isOpened() else "inactive",
            "has_frame": latest_frame is not None
        })


    if __name__ == "__main__":
        print("🚀 Server chạy tại: http://127.0.0.1:5000")
        print("📹 Truy cập để xem camera và logs")
        print("🔍 Debug camera: http://127.0.0.1:5000/camera_status")
        app.run(debug=True, threaded=True, use_reloader=False)
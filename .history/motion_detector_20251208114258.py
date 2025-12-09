import cv2
import numpy as np
import requests
import time
from datetime import datetime
from controller import report_motion

STREAM_URL = "http://127.0.0.1:5000/video_feed"

print("📡 Motion Detector đang chạy...")
print("Nhấn CTRL + C để dừng.\n")

last_frame = None

# Đọc stream từ server
stream = requests.get(STREAM_URL, stream=True)
bytes_buffer = b""

for chunk in stream.iter_content(chunk_size=1024):
    bytes_buffer += chunk
    a = bytes_buffer.find(b"\xff\xd8")  # JPEG start
    b = bytes_buffer.find(b"\xff\xd9")  # JPEG end

    if a != -1 and b != -1:
        jpg = bytes_buffer[a:b+2]
        bytes_buffer = bytes_buffer[b+2:]

        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

        if frame is None:
            print("⚠ Frame decode lỗi")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_frame is None:
            last_frame = gray
            continue

        # Tính sự khác biệt
        diff = cv2.absdiff(last_frame, gray)
        thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False

        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue
            motion_detected = True

        if motion_detected:
            print("🐾 Chuyển động phát hiện!")
            report_motion()

        last_frame = gray

        # Hiển thị ra cho debug
        cv2.imshow("Motion Detector", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cv2.destroyAllWindows()

import cv2
from arduino_sim import ArduinoSimulator

# Khởi tạo mô phỏng Arduino
arduino = ArduinoSimulator()

# Mở camera laptop (0 là camera mặc định)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Không thể mở camera!")
    exit()

last_frame = None

print("Hệ thống PIR (mô phỏng bằng camera) đang chạy...")
print("Nhấn Q để thoát.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Không lấy được khung hình từ camera!")
        break

    # Chuyển sang ảnh xám & làm mờ
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Lưu frame đầu tiên làm chuẩn so sánh
    if last_frame is None:
        last_frame = gray
        continue

    # Tính độ chênh lệch giữa 2 frame
    frame_diff = cv2.absdiff(last_frame, gray)
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]

    # Tìm vùng chuyển động
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) < 1500:
            continue  # bỏ các nhiễu nhỏ

        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Gửi tín hiệu vào Arduino mô phỏng
        arduino.receive_signal("Chuyển động được ghi nhận")

    last_frame = gray

    # Hiển thị camera
    cv2.imshow("Camera Feed (PIR mô phỏng)", frame)

    # Nhấn Q để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Giải phóng tài nguyên
cap.release()
cv2.destroyAllWindows()

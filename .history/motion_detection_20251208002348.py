import cv2

# Mở camera laptop (thường là thiết bị 0)
cap = cv2.VideoCapture(0)

# Khởi tạo biến lưu trữ ảnh cũ
last_frame = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Chuyển ảnh sang đen trắng
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Nếu không có ảnh cũ, lưu ảnh đầu tiên
    if last_frame is None:
        last_frame = gray
        continue

    # Tính sự khác biệt giữa ảnh hiện tại và ảnh cũ
    frame_diff = cv2.absdiff(last_frame, gray)
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]

    # Xác định sự chuyển động nếu có
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        if cv2.contourArea(contour) < 500:  # Điều chỉnh ngưỡng để loại bỏ nhiễu
            continue

        # Vẽ đường bao quanh chuyển động
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # In ra thông báo nếu phát hiện chuyển động
        print("Chuyển động phát hiện!")

    # Cập nhật ảnh cũ
    last_frame = gray

    # Hiển thị video
    cv2.imshow("Camera Feed", frame)

    # Thoát khi nhấn phím 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

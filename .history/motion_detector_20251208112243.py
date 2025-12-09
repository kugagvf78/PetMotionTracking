import cv2
from arduino_sim import ArduinoSimulator

arduino = ArduinoSimulator()
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Không tìm thấy camera!")
    exit()

last_frame = None

print("📡 Motion Detector đang chạy...")
print("Nhấn Q để thoát.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if last_frame is None:
        last_frame = gray
        continue

    # chênh lệch frame (giống PIR phát hiện)
    diff = cv2.absdiff(last_frame, gray)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]

    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) < arduino.sensitivity:
            continue

        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        arduino.receive_signal("Chuyển động được ghi nhận")

    last_frame = gray

    cv2.imshow("PIR mô phỏng (Camera)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

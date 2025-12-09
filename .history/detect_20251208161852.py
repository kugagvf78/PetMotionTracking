from ultralytics import YOLO
import cv2

MODEL_PATH = r"runs/detect/train/weights/best.pt"  # đường dẫn model sau khi train

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.5)

    annotated = results[0].plot()

    cv2.imshow("Pet Detector", annotated)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

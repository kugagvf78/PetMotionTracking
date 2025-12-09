from ultralytics import YOLO
import cv2

# Load model bạn đang dùng trong server
model = YOLO("runs/detect/train/weights/best.pt")

# Load ảnh test
img = cv2.imread("test.jpg")   # đổi tên file đúng ảnh bạn muốn test

# Detect
results = model.predict(img, conf=0.15, show=True)

print(results)

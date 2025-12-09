from ultralytics import YOLO
import cv2

model = YOLO("runs/detect/train/weights/best.pt")

img = cv2.imread("dog.jpg")
results = model.predict(img, conf=0.15, show=True)

print(results)

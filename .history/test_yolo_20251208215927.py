from ultralytics import YOLO
import cv2

model = YOLO("runs/detect/train/weights/best.pt")
results = model.predict("test.jpg", conf=0.05)

for r in results:
    print("Boxes:", r.boxes)
    print("Scores:", [float(b.conf[0]) for b in r.boxes])
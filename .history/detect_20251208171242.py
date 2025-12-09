from ultralytics import YOLO
import numpy as np

class PetDetector:
    def __init__(self):
        MODEL_PATH = "runs/detect/train/weights/best.pt"
        self.model = YOLO(MODEL_PATH)

    def detect(self, frame):
        # Chạy YOLO
        results = self.model(frame, conf=0.5, verbose=False)

        if len(results[0].boxes) == 0:
            return "None", 0.0

        box = results[0].boxes[0]
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        label = results[0].names[cls_id]  # “Cat” hoặc “Dog”
        return label, conf

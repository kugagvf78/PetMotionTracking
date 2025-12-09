from ultralytics import YOLO
import numpy as np

class PetDetector:
    def __init__(self, model_path="models/best.pt"):
        print("🔍 Loading YOLO Pet Detector...")
        self.model = YOLO(model_path)
        self.class_names = self.model.names  # ví dụ {0: 'cat', 1: 'dog'}

    def detect(self, frame):
        """Trả về (label, confidence) hoặc (None, 0)"""
        results = self.model(frame, conf=0.5)

        if len(results[0].boxes) == 0:
            return None, 0

        box = results[0].boxes[0]
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        label = self.class_names[cls]

        return label, conf

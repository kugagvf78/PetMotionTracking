from ultralytics import YOLO

class PetDetector:
    def __init__(self):
        MODEL_PATH = "runs/detect/train/weights/best.pt"
        self.model = YOLO(MODEL_PATH)

    def detect(self, frame):
        # Chạy YOLO 1 FRAME DUY NHẤT — KHÔNG LOOP, KHÔNG MỞ CAMERA
        results = self.model.predict(frame, conf=0.5, verbose=False)

        # Không có detection
        if len(results[0].boxes) == 0:
            return "None", 0.0

        # Lấy detection đầu
        box = results[0].boxes[0]
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        label = results[0].names[cls_id]  # “cat”, “dog”
        return label, conf

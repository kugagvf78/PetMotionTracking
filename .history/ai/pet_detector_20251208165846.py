# ai/pet_detector.py
from ultralytics import YOLO
import cv2

class PetDetector:
    def __init__(self):
        # Load model đã train
        self.model = YOLO("runs/detect/train/weights/best.pt")

        # Tên class phải trùng với YAML: ['Cat', 'Dog']
        self.class_names = ["Cat", "Dog"]

    def detect(self, frame):
        """
        Trả về:
        - label: tên thú cưng (Cat / Dog / None)
        - conf: độ tự tin (0.0 nếu không detect)
        """

        results = self.model(frame, verbose=False)

        if len(results[0].boxes) == 0:
            return "None", 0.0

        # lấy box có confidence cao nhất
        box = results[0].boxes[0]

        cls_id = int(box.cls[0])
        label = self.class_names[cls_id]
        conf = float(box.conf[0])

        # ------- VẼ BOX LÊN FRAME -------
        xyxy = box.xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = xyxy

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return label, conf

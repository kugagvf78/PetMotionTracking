import cv2
import numpy as np
import os

class PetDetector:
    def __init__(self):
        self.model_path = "ai_models/pet_yolov5.onnx"

        if not os.path.exists(self.model_path):
            print("⚠️ Không tìm thấy model ONNX – chuyển sang chế độ Fake AI.")
            self.model = None
            self.fake = True
            return
        
        print("🔧 Loading Pet Detector ONNX model...")
        self.net = cv2.dnn.readNet(self.model_path)
        self.fake = False

        # Labels (tùy theo model)
        self.labels = ["cat", "dog"]

    def detect(self, frame):
        """
        Trả về:
          - label: "cat", "dog", hoặc None
          - confidence: float
        """

        if self.fake:
            # Fake AI khi không có model thật
            return None, 0.0

        try:
            blob = cv2.dnn.blobFromImage(
                frame, 1/255.0, (640, 640),
                swapRB=True, crop=False
            )

            self.net.setInput(blob)
            preds = self.net.forward()

            # YOLO output: (1, num_boxes, 85)
            preds = preds[0]

            best_conf = 0
            best_label = None

            for det in preds:
                confidence = det[4]
                if confidence < 0.5:
                    continue

                class_scores = det[5:]
                class_id = np.argmax(class_scores)
                score = class_scores[class_id]

                if score > best_conf:
                    best_conf = score
                    best_label = self.labels[class_id]

            return best_label, float(best_conf)

        except Exception as e:
            print("❌ PetDetector error:", e)
            return None, 0.0

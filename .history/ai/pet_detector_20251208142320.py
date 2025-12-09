import requests
import cv2
import base64

API_URL = "https://serverless.roboflow.com/iot-eprbe/workflows/find-pets"
API_KEY = "YOUR_API_KEY"

class PetDetector:

    def detect(self, frame):
        # nén ảnh nhỏ để gửi lên API
        resized = cv2.resize(frame, (320, 320))
        _, buffer = cv2.imencode(".jpg", resized)
        img_str = base64.b64encode(buffer).decode("utf-8")

        payload = {
            "api_key": API_KEY,
            "inputs": {
                "image": {"type": "base64", "value": img_str}
            }
        }

        res = requests.post(API_URL, json=payload)
        data = res.json()

        try:
            objs = data["predictions"]  # tùy vào workflow response
            if len(objs) > 0:
                return True, objs[0]
        except:
            return False, None

        return False, None

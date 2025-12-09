import cv2
import numpy as np

class AIMotionDetector:
    def __init__(self):
        self.prev_frame = None

    def detect(self, frame):
        """
        Trả về True nếu có chuyển động.
        Trả về False nếu không có gì.
        """

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Lần đầu chạy → lưu frame cũ
        if self.prev_frame is None:
            self.prev_frame = gray
            return False

        # So sánh frame hiện tại với frame trước đó
        diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # tìm contour
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        motion_detected = False

        for c in contours:
            if cv2.contourArea(c) > 800:  # threshold lọc nhiễu
                motion_detected = True
                break

        # Cập nhật frame cũ
        self.prev_frame = gray

        return motion_detected

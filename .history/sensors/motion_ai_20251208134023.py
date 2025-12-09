import cv2
import numpy as np

class MotionAIDetector:
    """
    AI-like motion detector using frame differencing.
    Returns a motion intensity value (0–100).
    """

    def __init__(self):
        self.prev_gray = None

    def detect(self, frame):
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_gray is None:
            self.prev_gray = gray
            return 0

        # Frame difference
        diff = cv2.absdiff(self.prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Contours = movement regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_value = 0

        for c in contours:
            area = cv2.contourArea(c)
            if area < 500:
                continue
            motion_value += area / 2000  # Normalize

        # Update previous frame
        self.prev_gray = gray

        # Cap result
        motion_value = min(int(motion_value), 100)

        return motion_value

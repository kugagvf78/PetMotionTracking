import cv2

class MotionAIDetector:
    def __init__(self):
        self.last_gray = None

    def detect(self, frame):
        # Convert to gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # First frame → no motion
        if self.last_gray is None:
            self.last_gray = gray
            return 0

        # Difference
        diff = cv2.absdiff(self.last_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_strength = 0

        for c in contours:
            if cv2.contourArea(c) < 500:  # sensitivity
                continue
            motion_strength += cv2.contourArea(c)

        # Update for next frame
        self.last_gray = gray

        return int(motion_strength)

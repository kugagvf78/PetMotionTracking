import cv2

def detect_motion_ai(frame):
    # Dùng background subtractor (bền vững hơn cách diff ảnh)
    fgbg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=50)

    fgmask = fgbg.apply(frame)
    cnts, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motions = []
    for c in cnts:
        if cv2.contourArea(c) > 800:
            motions.append(c)

    return len(motions) > 0

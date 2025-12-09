import time

last_positions = []
last_move_time = time.time()

def detect_behavior(pet_detected, motion_detected, rfid_zone):
    global last_positions, last_move_time

    behavior = "Unknown"

    if not pet_detected:
        return "No Pet"

    if motion_detected:
        behavior = "Moving"
        last_move_time = time.time()
    else:
        if time.time() - last_move_time > 30:
            behavior = "Sleeping / Inactive"
        else:
            behavior = "Idle"

    if rfid_zone == "feeding_zone":
        behavior = "Eating"

    return behavior

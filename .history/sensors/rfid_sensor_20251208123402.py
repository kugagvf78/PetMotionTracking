import random

PET_TAG = "PET-001"

def read_rfid():
    zones = ["feeding_zone", "sleep_zone", "play_zone", None]

    # Ngẫu nhiên thú cưng đi vào khu vực nào đó
    return random.choice(zones)

import time
import requests
import random

SERVER = "http://127.0.0.1:5000"

def simulate_pir():
    pir_value = random.choice([0, 1])
    requests.post(f"{SERVER}/update_pir", json={"pir": pir_value})
    print("📡 PIR gửi:", pir_value)


def simulate_rfid():
    tag = random.choice(["PET001", "PET002", "CAT123", "DOG789"])
    requests.post(f"{SERVER}/update_rfid", json={"rfid": tag})
    print("🎯 RFID quét:", tag)


while True:
    action = random.choice(["pir", "rfid", "none"])

    if action == "pir":
        simulate_pir()

    elif action == "rfid":
        simulate_rfid()

    time.sleep(3)   # gửi mỗi 3 giây

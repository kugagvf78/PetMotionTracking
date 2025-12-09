import time

class ArduinoSimulator:
    def __init__(self):
        self.last_signal_time = None

    def receive_signal(self, message):
        """Mô phỏng Arduino nhận tín hiệu từ PIR."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_signal_time = timestamp

        print(f"[Arduino] {timestamp} → {message}")

        with open("motion_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {message}\n")

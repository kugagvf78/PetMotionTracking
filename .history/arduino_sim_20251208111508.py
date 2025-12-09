import time

class ArduinoSimulator:
    def __init__(self):
        self.last_signal_time = None

    def receive_signal(self, message):
        """Mô phỏng Arduino nhận tín hiệu từ cảm biến PIR."""
        self.last_signal_time = time.strftime("%Y-%m-%d %H:%M:%S")

        print(f"[Arduino] Nhận tín hiệu PIR → {message}")

        with open("motion_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{self.last_signal_time} - {message}\n")

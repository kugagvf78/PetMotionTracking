import time

class ArduinoSimulator:
    def __init__(self):
        self.sensitivity = 1500  # mặc định
        self.log_enabled = True

    def update_settings(self, sensitivity, log_enabled):
        self.sensitivity = int(sensitivity)
        self.log_enabled = bool(log_enabled)
        print(f"[Arduino] Sensitivity={self.sensitivity}, Logging={self.log_enabled}")

    def receive_signal(self, message):
        """Mô phỏng Arduino nhận tín hiệu từ PIR."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if self.log_enabled:
            print(f"[Arduino] {timestamp} → {message}")

            with open("motion_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - {message}\n")

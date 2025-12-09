import os
from datetime import datetime

LOG_FILE = "motion_log.txt"

def report_motion():
    """Ghi lại chuyển động vào file log."""
    if not os.path.exists(LOG_FILE):
        # tạo file nếu chưa có
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            pass

    time_stamp = datetime.now().strftime("%H:%M:%S")
    message = f"{time_stamp} - Chuyển động được ghi nhận!"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

    print("📌 LOG:", message)

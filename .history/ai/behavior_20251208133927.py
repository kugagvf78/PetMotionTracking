# ai/behavior.py

import time

class BehaviorAnalyzer:
    """
    Phân tích hành vi thú cưng dựa trên:
    - Mức độ chuyển động
    - Thời gian không hoạt động
    - Tần suất chuyển động
    """

    def __init__(self):
        self.last_motion_time = time.time()
        self.motion_history = []  # Lưu mức độ chuyển động 20 lần gần nhất
        self.behavior_score = 0

    def update(self, motion_level):
        """
        motion_level:
            0 = không chuyển động
            1 = chuyển động nhẹ
            2 = chuyển động mạnh
        """

        now = time.time()

        # Ghi lại lịch sử (giới hạn 20 phần tử)
        self.motion_history.append(motion_level)
        if len(self.motion_history) > 20:
            self.motion_history.pop(0)

        # Cập nhật last motion
        if motion_level > 0:
            self.last_motion_time = now

        # Tính điểm hành vi (0–100)
        # Chuyển động mạnh cho điểm cao hơn
        self.behavior_score = int(
            sum(self.motion_history) / (len(self.motion_history) * 2) * 100
        )

        # Phân tích hành vi
        return self.analyze(now)

    def analyze(self, now):
        """ Trả về phân tích hành vi """
        time_since_last_motion = now - self.last_motion_time

        status = "bình thường"
        alert = None

        # Nếu không chuyển động quá 30 giây -> có thể ngủ
        if time_since_last_motion > 30 and self.behavior_score < 20:
            status = "đang nghỉ"
        
        # Nếu không chuyển động quá 120 giây -> có thể bất thường
        if time_since_last_motion > 120:
            alert = "⚠️ Không phát hiện chuyển động hơn 2 phút!"

        # Nếu activity ≥ 70% -> thú cưng đang chạy nhảy mạnh
        if self.behavior_score > 70:
            status = "rất hiếu động"
            if self.behavior_score > 85:
                alert = "🔥 Pet đang hoạt động bất thường (quá mức)!"

        return {
            "score": self.behavior_score,
            "status": status,
            "alert": alert,
            "idle_time": int(time_since_last_motion)
        }

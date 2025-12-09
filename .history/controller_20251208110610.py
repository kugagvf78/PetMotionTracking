def report_motion():
    print("Arduino mô phỏng: Nhận tín hiệu PIR → Có chuyển động!")
    with open("motion_log.txt", "a", encoding="utf-8") as f:
        f.write("Chuyển động được ghi nhận!\n")
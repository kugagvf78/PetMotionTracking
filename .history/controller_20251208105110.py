def report_motion():
    print("Arduino mô phỏng: Nhận tín hiệu PIR → có chuyển động!")
    with open("motion_log.txt", "a") as f:
        f.write("Chuyển động được ghi nhận!\n")

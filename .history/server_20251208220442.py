# ================================
# YOLO PET DETECTION — FIXED 100%
# ================================
pet_label = "Không thấy"
pet_conf = 0.00

try:
    # chạy y chang test_yolo: conf thấp để test
    results = PET_MODEL.predict(frame, conf=0.03, verbose=False)

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = PET_MODEL.names[cls]

            # debug: xem YOLO detect được gì
            print("YOLO DETECT:", label, conf)

            # nếu conf thấp -> vẫn vẽ box
            if conf >= 0.03:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                # vẽ box vàng
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
                cv2.putText(frame,
                            f"{label} {conf:.2f}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 255),
                            2)

                pet_label = label
                pet_conf = conf

except Exception as e:
    print("🔥 Lỗi YOLO:", e)

# Overlay thông tin thú cưng (luôn hiện)
cv2.putText(frame,
            f"Pet: {pet_label} ({pet_conf:.2f})",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 200, 0),
            2)

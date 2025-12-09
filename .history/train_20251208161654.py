from ultralytics import YOLO

# === CHỈ SỬA DÒNG NÀY ===
DATASET_PATH = r"D:\HUIT\HK7\IOT\DoAndogs_vs_cats\data.yaml"
# ========================

print("🚀 Training YOLO model...")

model = YOLO("yolov8n.pt")  # model nhẹ nhất

model.train(
    data=DATASET_PATH,
    epochs=50,
    imgsz=640,
    batch=8,
)

print("🎉 Training completed! Check: runs/detect/train/weights/best.pt")

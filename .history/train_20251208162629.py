from ultralytics import YOLO

model = YOLO("yolov8n.pt")   # dùng model base để train

model.train(
    data="datasets/pets/data.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
)
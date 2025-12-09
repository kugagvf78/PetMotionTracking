from ultralytics import YOLO

model = YOLO("yolov8n.pt")

model.train(
    data="D:/datasets/dogs_vs_cats/data.yaml",
    epochs=50,
    imgsz=640
)

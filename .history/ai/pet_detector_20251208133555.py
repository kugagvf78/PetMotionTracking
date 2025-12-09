import cv2

net = cv2.dnn.readNetFromONNX("ai_models/cat_detector.onnx")

def detect_pet(frame):
    blob = cv2.dnn.blobFromImage(frame, 1/255, (224, 224))
    net.setInput(blob)
    out = net.forward()

    class_id = out.argmax()
    confidence = out.max()

    if confidence > 0.6:
        label = "Cat" if class_id == 0 else "Dog"
        return label, confidence
    
    return None, 0

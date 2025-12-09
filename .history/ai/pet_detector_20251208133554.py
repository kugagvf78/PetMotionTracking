import random

class PetDetector:
    """
    Mô phỏng AI nhận diện thú cưng.
    Không cần model thật, không cần ONNX.
    Trả về True khoảng 10% số lần — đủ để demo.
    """

    def __init__(self):
        pass

    def detect(self, frame):
        # Tỉ lệ nhận diện để system trông giống thật
        # M muốn tỉ lệ cao/thấp hơn thì chỉnh.
        return random.choice([True, False, False, False, False])

import random
import time

def read_pir():
    # 20% xác suất có chuyển động
    return 1 if random.random() < 0.2 else 0

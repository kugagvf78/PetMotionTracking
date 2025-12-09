import random

class PIRSensor:
    def read(self):
        return random.choice([0,0,0,1])  # 25% trigger

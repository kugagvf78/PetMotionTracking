import random
import time

class PIRSensor:
    """
    Simulated PIR motion sensor.
    """

    def __init__(self):
        self.last_state = False

    def read_motion(self):
        """
        Randomly simulate PIR motion detection.
        Returns True or False.
        """
        time.sleep(0.1)
        self.last_state = random.choice([False, False, False, True])  # 25% chance
        return self.last_state

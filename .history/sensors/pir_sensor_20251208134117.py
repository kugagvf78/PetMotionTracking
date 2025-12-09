import random
import time

class PIRSensor:
    """
    Simulated PIR motion sensor.
    """

    def __init__(self):
        self.last_state = False

    def read(self):
        """
        Random simulation — return True when motion detected.
        Replace with real GPIO code when using ESP8266 or Arduino.
        """
        time.sleep(0.1)
        self.last_state = random.choice([False, False, True])  # 1/3 chance
        return self.last_state

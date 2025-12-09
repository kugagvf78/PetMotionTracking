import time
import random

class RFIDSensor:
    """
    Simulated RFID reader.
    Returns tag IDs occasionally.
    """

    TAGS = ["PET123", "DOG887", "CAT552", None, None]

    def __init__(self):
        self.last_tag = None

    def read(self):
        """
        Randomly return an RFID tag (simulate ESP8266/Arduino RFID reader)
        """
        time.sleep(0.2)
        tag = random.choice(self.TAGS)
        self.last_tag = tag
        return tag

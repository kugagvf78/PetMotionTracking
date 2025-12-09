import random

class RFIDReader:
    tags = ["PET123", "PET999", None, None, None]

    def read(self):
        return random.choice(self.tags)

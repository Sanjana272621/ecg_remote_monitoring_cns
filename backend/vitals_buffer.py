class VitalsBuffer:
    def __init__(self):
        self.latest = {}

    def update(self, packet):
        self.latest = packet.copy()

    def get(self):
        return self.latest
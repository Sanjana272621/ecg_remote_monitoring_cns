class VitalsBuffer:
    def __init__(self):
        self.latest_vitals = {}

    def update(self, vitals, timestamp):
        for code, values in vitals.items():
            self.latest_vitals[code] = {
                "name": values["name"],
                "value": values["value"],
                "unit": values["unit"],
                "timestamp": timestamp
            }

    def view(self):
        for code, values in self.latest_vitals.items():
            print(f"{code}: {values}")

    def get(self):
        return self.latest_vitals
#when overwrite, read pointer increments
#when data comes close to being overwritten => leads are removed
# need to force plot 0
 
class CircularBuffer:
    def __init__(self, size):
        self.size = size
        self.data = [None] * size

        self.write = 0
        self.read = -1

        self.count = 0

    def update(self, batch):

        for item in batch:
            self.data[self.write] = item

            self.write = (self.write + 1) % self.size

            if self.count < self.size:
                self.count += 1
            else:
                self.read = (self.read +1)%self.size

    def get_latest(self, sample_count):
        if self.count == 0:
            return []

        latest = []

        for _ in range(min(sample_count, self.count)): #Sends 5 sampels each update
            self.read = (self.read + 1) % self.size
            latest.append(self.data[self.read])

            self.count -= 1

        return latest

    def get_window(self, sample_count):
        if self.count == 0:
            return [0]

        latest = []
        temp = self.read 

        for _ in range(min(sample_count, self.count)):
            temp = (temp + 1) % self.size
            latest.append(self.data[temp])

        return latest
    
    def get_count(self):
        return self.count
    
    def clear(self, size):
        self.size = size
        self.data = [None] * size

        self.write = 0
        self.read = -1

        self.count = 0

        

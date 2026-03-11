class LongMemory:

    def __init__(self, storage):
        self.storage = storage

    def save_event(self, event):
        self.storage.append(event)

    def retrieve(self):
        return self.storage

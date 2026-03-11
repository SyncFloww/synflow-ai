class AgentMemory:

    def __init__(self):
        self.history = []

    def add(self, message):
        self.history.append(message)

    def get_context(self):
        return "\n".join(self.history[-5:])

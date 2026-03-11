class MemoryAgent:
    """
    Stores knowledge across the platform. Remembers brand constraints, previous conversations,
    and user preferences.
    """

    def __init__(self):
        self.conversations = {}
        self.brand_voices = {}

    def get_brand_voice(self, brand_name):
        return self.brand_voices.get(brand_name, "Professional and helpful")

    def set_brand_voice(self, brand_name, voice):
        self.brand_voices[brand_name] = voice

    def get_conversation_context(self, session_id):
        history = self.conversations.get(session_id, [])
        return "\n".join(history[-5:])

    def add_interaction(self, session_id, message):
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        self.conversations[session_id].append(message)

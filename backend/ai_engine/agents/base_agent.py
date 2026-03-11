class Agent:
    """
    Base Agent class for SyncflowAI
    """

    def __init__(self, name="SyncflowAgent"):
        self.name = name

    def read_input(self, user_input: str):
        """
        Receive input from user, system, or automation rule
        """
        print(f"[{self.name}] Reading input...")
        return user_input

    def think(self, input_text: str):
        """
        Process the input and decide what to do
        (Later this will call the LLM)
        """
        print(f"[{self.name}] Thinking...")
        thought = f"I should respond to: {input_text}"
        return thought

    def respond(self, thought: str):
        """
        Generate the final response
        """
        print(f"[{self.name}] Responding...")
        response = f"Agent response: {thought}"
        return response

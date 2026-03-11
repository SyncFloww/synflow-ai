class SocialAgent:

    def __init__(self, llm, tools, memory):
        self.llm = llm
        self.tools = tools
        self.memory = memory

    def read_input(self, text):
        self.memory.add(text)
        return text

    def understand_context(self, text):
        return f"Analyze intent of: {text}"

    def think(self):
        context = self.memory.get_context()
        prompt = f"""
        Conversation context:
        {context}

        Decide how to respond.
        """
        return self.llm.generate(prompt)

    def choose_tool(self, thought):
        if "reply" in thought.lower():
            return "reply_tool"
        if "post" in thought.lower():
            return "post_tool"
        return None

    def execute_tool(self, tool_name, input_text):
        if tool_name in self.tools:
            return self.tools[tool_name](input_text)
        return "No tool used"

    def respond(self, result):
        return result

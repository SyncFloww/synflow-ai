from core.llm_agents.prompts import SYSTEM_PROMPT


class SyncflowAgent:

    def __init__(self, llm):
        self.llm = llm
        self.system_prompt = SYSTEM_PROMPT

    def read_input(self, user_input: str):
        return user_input

    def build_prompt(self, user_input):

        prompt = f"""
{self.system_prompt}

User request:
{user_input}
"""

        return prompt

    def think(self, user_input):

        prompt = self.build_prompt(user_input)

        response = self.llm(prompt)

        return response

    def respond(self, response):
        return response

    def run(self, user_input):

        data = self.read_input(user_input)

        thoughts = self.think(data)

        output = self.respond(thoughts)

        return output

from core.llm_agents.prompt_builder import build_prompt

class SalesAgent:
    """
    Converts interest into revenue by answering product questions and promoting offers.
    """

    def __init__(self, llm):
        self.llm = llm

    def handle_inquiry(self, message, brand=None):
        prompt = build_prompt(f"Handle this sales-related inquiry: '{message}'. Include product details/links if requested.", brand_name=brand)
        return self.llm(prompt)

from core.llm_agents.prompt_builder import build_prompt

class EngagementAgent:
    """
    Handles comments and community interaction.
    """

    def __init__(self, llm):
        self.llm = llm

    def reply_to_comment(self, comment_text, brand=None):
        prompt = build_prompt(f"Reply to this user comment: '{comment_text}'", brand_name=brand)
        return self.llm(prompt)

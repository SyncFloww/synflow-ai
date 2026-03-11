from core.llm_agents.prompt_builder import build_prompt

class ContentAgent:
    """
    Creates posts, captions, and campaigns.
    """
    
    def __init__(self, llm):
        self.llm = llm

    def generate_post(self, topic, brand=None):
        prompt = build_prompt(f"Create a social media post about: {topic}", brand_name=brand)
        return self.llm(prompt)

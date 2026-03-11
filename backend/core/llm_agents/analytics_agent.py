from core.llm_agents.prompt_builder import build_prompt

class AnalyticsAgent:
    """
    Reads performance data and provides insights.
    """

    def __init__(self, llm):
        self.llm = llm

    def analyze_data(self, data_summary, brand=None):
        prompt = build_prompt(f"Analyze the following performance data and provide actionable marketing insights: {data_summary}", brand_name=brand)
        return self.llm(prompt)

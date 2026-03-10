from ai_engine.agents.base_agent import BaseAgent
from ai_engine.tools.social_poster import post_to_social_media, fetch_trending_topics

class SocialMediaAgent(BaseAgent):
    """
    An agent configured with specific capabilities to write and publish 
    content to social media.
    """
    def __init__(self, agent_model):
        super().__init__(agent_model)
        
        # We explicitly supply tools so the agent knows what it can do
        self.tools = [
            post_to_social_media, 
            fetch_trending_topics
        ]
        
    def execute(self, task_input):
        """
        Runs the actual agent logic given some input from an AgentTask.
        """
        executor = self.build_agent_executor()
        
        try:
            # Tell the agent to process the input based on its tools/memory
            result = executor.run(task_input)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

import json
from core.llm_agents.memory import AgentMemory
from core.llm_agents.prompt_builder import build_prompt
from core.llm_agents.reasoner import AgentReasoner
from core.llm_agents.tools import AgentTools
from core.services.automation_engine import AutomationEngine

class SyncflowAgent:

    def __init__(self, llm):
        self.llm = llm
        self.memory = AgentMemory()
        self.reasoner = AgentReasoner()
        self.tools = AgentTools()
        self.automation = AutomationEngine()

    def run(self, user_input, brand=None):
        # 1. Memory Context
        context = self.memory.get_context()
        
        # 2. Prompt Builder
        combined_input = f"{context}\nUser Request: {user_input}"
        prompt = build_prompt(combined_input, brand_name=brand)
        
        # 3. LLM Generation
        response_json_str = self.llm(prompt)
        
        try:
            response_data = json.loads(response_json_str)
        except json.JSONDecodeError:
            response_data = {
                "thought": "Failed to parse JSON",
                "action": "error",
                "response": response_json_str
            }
            
        # 4. Reasoner (Validate or overwrite action based on response content)
        task_action = self.reasoner.analyze(response_data.get("response", ""))
        response_data["action"] = task_action
        
        # 5. Automation / Tools execution stub
        self.automation.trigger(task_action, response_data)

        # 6. Save to memory
        self.memory.add(user_input)

        return response_data

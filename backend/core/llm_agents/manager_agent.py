class ManagerAgent:
    """
    The Orchestrator agent that decides which specialized agent should handle the task.
    """

    def route(self, user_input):
        input_lower = user_input.lower()
        
        if "comment" in input_lower or "reply" in input_lower:
            return "engagement"

        if "post" in input_lower or "caption" in input_lower:
            return "content"

        if "buy" in input_lower or "price" in input_lower or "cost" in input_lower:
            return "sales"
            
        if "analyze" in input_lower or "insight" in input_lower or "performance" in input_lower:
            return "analytics"

        return "general"

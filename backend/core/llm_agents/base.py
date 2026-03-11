import json

class DummyLLM:
    """
    Temporary LLM wrapper mimicking structured JSON outputs
    """

    def __call__(self, prompt: str):
        # Extract user request to make dummy output slightly dynamic
        user_req = "Unknown request"
        if "User request:" in prompt:
            user_req = prompt.split("User request:")[-1].strip()
            
        response_data = {
            "thought": f"Agent reasoning about: {user_req}",
            "action": "execute_task",
            "response": f"Mock generated response for: {user_req}"
        }
        return json.dumps(response_data, indent=2)

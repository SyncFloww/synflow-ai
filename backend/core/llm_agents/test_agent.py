from core.llm_agents.agent import SyncflowAgent
from core.llm_agents.base import DummyLLM
import json

def run_test():

    llm = DummyLLM()
    agent = SyncflowAgent(llm)

    tests = [
        ("Write a reply to this comment: 'Love the new sneakers'", "Nike"),
        ("Send a welcoming DM to the new follower", "Nike"),
        ("Analyze this review: 'Your service is terrible'", "Syncflow Support")
    ]

    print("========= PRODUCTION AGENT TEST =========")
    for user_input, brand in tests:
        print(f"\n--- Processing for Brand: {brand} ---")
        print(f"Input: {user_input}")
        
        result = agent.run(user_input, brand=brand)
        
        print(f"Agent Memory Size: {len(agent.memory.history)}")
        print("Final Output:")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_test()

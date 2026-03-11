from core.llm_agents.agent import SyncflowAgent
from core.llm_agents.base import DummyLLM

def run_test():

    llm = DummyLLM()
    agent = SyncflowAgent(llm)

    # Core required tests from March 14 payload
    tests = [
        "Write a reply thanking a new follower",
        "Create a caption promoting a new product",
        "Analyze this comment sentiment:\n\"I hate this service\""
    ]

    for i, test_input in enumerate(tests, 1):
        print(f"\n{'='*15} TEST {i} {'='*15}")
        print(f"Input:\n{test_input}\n")
        result = agent.run(test_input)
        print("Expected Output Format:")
        print(result)

if __name__ == "__main__":
    run_test()

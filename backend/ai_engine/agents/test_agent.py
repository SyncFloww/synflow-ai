from base_agent import Agent

def run_test():
    agent = Agent()
    user_input = "Write a tweet announcing SyncflowAI."
    step1 = agent.read_input(user_input)
    step2 = agent.think(step1)
    step3 = agent.respond(step2)

    print("\nFINAL OUTPUT")
    print(step3)

if __name__ == "__main__":
    run_test()

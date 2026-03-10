from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from ai_engine.llm.deepseek import get_deepseek_llm

class BaseAgent:
    """
    Base class for initializing LangChain agents with the target LLM and memory.
    """
    def __init__(self, agent_model):
        """
        :param agent_model: The Django `Agent` database model instance 
                            that holds configuration like the system prompt.
        """
        self.agent_config = agent_model
        # Use our loaded DeepSeek instance
        self.llm = get_deepseek_llm()
        
        # Every agent instance should have basic conversational memory 
        # so it doesn't forget context.
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )

        self.tools = []

    def get_system_prompt(self):
        """
        Builds the system instructions using the Brand and Agent definitions in the DB.
        """
        brand_context = f"Brand Tone of Voice: {self.agent_config.brand.tone_of_voice}" if hasattr(self.agent_config.brand, 'tone_of_voice') else ""
        system_instruction = f"{self.agent_config.system_prompt}\n\n{brand_context}"
        return system_instruction

    def build_agent_executor(self):
        """
        Wraps the LLM, Tools, and Memory into an executable LangChain Agent.
        """
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True, # Will output its thoughts to the celery worker logs
            agent_kwargs={
                "system_message": self.get_system_prompt()
            }
        )

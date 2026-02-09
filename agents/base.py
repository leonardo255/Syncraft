from abc import abstractmethod
from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver


class Agent:
    def __init__(self, role, version, sys_prompt, tools, model):
        self.role           = role
        self.version        = version
        self.model          = model
        self.tools          = tools
        self.sys_prompt     = sys_prompt
        self.checkpointer   = InMemorySaver()
        self.init_agent()

    def init_agent(self):
        # Init agent
        self.agent = create_agent(
            model           = self.model,
            tools           = self.tools,
            system_prompt   = self.sys_prompt,
            checkpointer    = self.checkpointer,
            middleware      = [],
        )

    def invoke(self, user_msg: HumanMessage):
        messages = [user_msg]
        response = self.agent.invoke(
            {"messages": messages},
            config={
                "configurable": {"thread_id": "1"},
                "max_concurrency": 1,     # 🔒 enforce sequential tool execution
            }
        )
        
        return response

    @abstractmethod
    def go_to_work(self, *args, **kwargs):
        """
        Abstract method for agent-specific logic:
        - Input preparation
        - Calling self.prompt()
        - Post-processing / merging metadata
        - Returning structured output
        """
        pass
from agents.base import Agent
from tools.simpy.inventory_control import run_simulation
from langchain.messages import AIMessage, HumanMessage
import os

class SimAgent(Agent):
    def __init__(self, model):
        sys_prompt = """
        You are an expert analyst simulating inventory control systems using the (s, S) policy.

        You have access to the following tools:
        - run_simulation: SimPy simulation of an (s, S) inventory control system. Returns a dict of cost metrics.

        Your goal:
        - Optimise the metric requested by the user. If the user does not specify a metric, follow up with the user to determine the metric to optimise.
        - You may run the simulation multiple times to find the optimal values for the (s, S) policy.
        - Between runs, analyse the results and reason about the next step.
        - In your final response, provide the final values for the (s, S) policy and the metric you optimised for.
        
        """
        super().__init__(
            role="Simulator",
            version="1.0",
            sys_prompt=sys_prompt,
            tools=[run_simulation],
            model=model
        )
    
    def go_to_work(self, user_instructions: str) -> str:

        user_msg = HumanMessage(content=user_instructions)
        result = self.invoke(user_msg=user_msg)

        # Extract final AI message
        messages = result.get("messages", [])
        final_msg = None

        if messages and isinstance(messages[-1], AIMessage):
            final_msg = messages[-1].content
        else:
            # fallback: find last AIMessage
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    final_msg = msg.content
                    break

        return final_msg
from abc import abstractmethod
from agents.config import DEFAULT_LLM_MODEL


class Agent:
    def __init__(self, role, version, sys_prompt, tools, client, model=DEFAULT_LLM_MODEL):
        self.role   = role
        self.version = version
        self.model  = model
        self.client = client
        self.tools  = tools
        self.messages = [
            {"role": "system", "content": sys_prompt}
        ]

    def prompt(self, user_input: str, parser=None):

        if parser:
            user_input += "\n\n" + parser.get_format_instructions()

        #self.messages.append({"role": "user", "content": user_input}) # Store chat history?

        messages = [
            *self.messages,
            {"role": "user", "content": user_input}
        ]

        response = self.client.chat.completions.create(
            model       = self.model,
            messages    = messages,
            tools       = self.tools,
            max_turns   = 5
        )
        output = response.choices[0].message.content.strip()
        #self.messages.append({"role": "assistant", "content": output}) # Store chat history?
        
        if parser:
            try:
                return parser.parse(output)
            except Exception as e:
                return {"error": f"Parser failed: {e}", "raw_output": output}
            
        return output
        

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
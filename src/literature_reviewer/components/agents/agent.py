"""
Agent class
Includes model calling, tool definition if necessary,
reflection, at agent/task level

In order to reflect, there is Agent-internal planning, 
execution, review, and if needed revision

"""
import datetime, logging
from pydantic import BaseModel
from typing import List
from literature_reviewer.components.agents.model_call import ModelInterface
from literature_reviewer.components.prompts.agent import general_agent_planning_sys_prompt
from datetime import datetime, timezone  # Add this import at the top of the file

class AgentPlan(BaseModel):
    steps: List[str]


class Task(BaseModel):
    action: str
    desired_result: str
    
    def as_markdown_string(self) -> str:
        return(
            f"""
                # Action
                {self.action}

                # Desired Result
                {self.desired_result}
            """
        )
        

class ConversationHistoryEntry(BaseModel):
    heading: str
    timestamp: str
    model: str
    content: str


class Agent:
    def __init__(
        self,
        name: str,
        task: Task,
        prior_context: str,
        model_interface: ModelInterface,
        system_prompt,
        tool,
        verbose,
        max_plan_steps=10
    ):
        self.model_interface = model_interface
        self.name = name
        self.task = task
        self.prior_context = prior_context
        self.system_prompt = system_prompt
        self.tool = tool
        self.verbose = verbose
        self.conversation_history = ""
        self.max_plan_steps = max_plan_steps
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.name}")
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        if self.prior_context:
            self.conversation_history += f"{self.prior_context}\n"
            self.logger.debug(f"Added prior context: {self.prior_context}")

    def add_to_conversation_history(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            heading = func.__name__
            content = str(result)
            timestamp = datetime.now(timezone.utc).isoformat()
            entry = f"\n{heading} ({timestamp}, {self.model_interface.model.model_name}):\n{content}\n"
            self.conversation_history += entry
            return result
        return wrapper

    @add_to_conversation_history
    def create_plan(self):
        """
        Gets agent-specific prompt for creating a step-by-step plan
        to accomplish the task within agent scope
        
        Tool use?
        """
        self.logger.debug("Starting planning process")
        return self.model_interface.chat_completion_call(
            system_prompt=general_agent_planning_sys_prompt(self.max_plan_steps),
            user_prompt=self.task.as_markdown_string()
        )

        
    @add_to_conversation_history    
    def enact_plan(self, plan):
        return self.tool.use()
    
    @add_to_conversation_history
    def review_plan():
        pass
    
    @add_to_conversation_history
    def revise_plan():
        pass
    
    def run(self):
        review_passed = False
        while not review_passed:
            plan = self.create_plan
            output = self.enact_plan
            
            
        
            
        
from typing import List, Any
from pydantic import BaseModel
from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.tools.basetool import ToolResponse, BaseTool
from literature_reviewer.tools.components.prompts.triage import generate_agent_task_list_sys_prompt

class AgentTaskDict(BaseModel):
    node: str
    task: str

class AgentTaskList(BaseModel):
    tasks: List[AgentTaskDict]

class TriageTool(BaseTool):
    """
    Triage Tool
    Generates a list of tasks for each agent provided to it
    """
    
    def __init__(self, model_interface: ModelInterface, available_agents: List[str], user_goal: str, max_tasks: int):
        super().__init__(model_interface)
        self.available_agents = available_agents
        self.user_goal = user_goal
        self.max_tasks = max_tasks

    def use(self, step: Any) -> ToolResponse:
        system_prompt = generate_agent_task_list_sys_prompt(
            agent_list=self.available_agents,
            user_goal=self.user_goal,
            max_tasks=self.max_tasks
        )

        # Extract the prompt from the step object
        user_prompt = step.prompt if hasattr(step, 'prompt') else str(step)

        agent_task_list = self.model_interface.chat_completion_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=AgentTaskList
        )
        
        return ToolResponse(
            output=agent_task_list,
            explanation="Task list generated based on planning step"
        )

from typing import List

def generate_agent_task_list_sys_prompt(agent_list: List[str], user_goal: str, max_tasks: int) -> str:
    return f"""
        Given a plan to create a task list, most likely something like "make a task list for each agent",
        do exactly that. 
        
        You are given these options of agents:
        {', '.join(agent_list)}
        
        Your job is to effectively allocate the abilities of each agent to solve the user's goal:
        {user_goal}
        
        The formatted output is an AgentTaskList. Each dictionary entry contains a "node" and a "task" field.
        
        This output should reflect the order of agents necessary to complete the task, and should use the minimal
        number of agents necessary to complete the task to the highest possible accuracy. At most the task list should
        contain {max_tasks} tasks. It can contain less if that is optimal, though - this is encouraged!
    """

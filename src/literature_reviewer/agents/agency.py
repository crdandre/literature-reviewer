"""
Agencies are teams of Agents
just like the CIA, but for writing systematic literature reviews
Can include reflection at the agency level (i.e., reviewer agent
gets outputs from all other agents, reviews them relative to reqs,
decides whether the task is complete...)

Possible hierarchies
1. Planner (o1 or CoT-encouraged 4o/sonnet) --> creates a list of subtasks
   suited to each agency member
2. Workers (Possible)
    1. Comprehension - encourages self-informed understanding of the task
    2. Anchoring
    3. Logic
    4. Cognition
    5. General
3. Aggregation
4. Verification

The weird/confusing bit is that each agent unto itself has reflection capabilities.
I'm probably banking on sentience arising from hierarchical reflection, or wasting
credits.

"""
from typing import List
from literature_reviewer.agents.agent import Agent

class Agency:
    def __init__(
        self,
        name: str,
        agents: Agent | List[Agent | List[Agent]],
    ):
        self.name = name
        self.agents = agents
        
        self._validate_agent_structure()
        
    def _validate_agent_structure(self):
        if not isinstance(self.agents, list):
            self.agents = [self.agents]
        
        if not isinstance(self.agents[0], Agent) or not isinstance(self.agents[-1], Agent):
            raise ValueError("The first and last items in agents must be single Agents.")
        
        for i, item in enumerate(self.agents[1:-1], start=1):
            if not isinstance(item, (Agent, list)) or (isinstance(item, list) and not all(isinstance(sub_item, Agent) for sub_item in item)):
                raise ValueError(f"Item at index {i} must be either an Agent or a list of Agents.")
        
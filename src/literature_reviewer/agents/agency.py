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


One possible way to go about this is:
Define agents sans what can be determined by a planning agent

    self.model_interface = model_interface
    self.name = name
    self.task = task
    self.prior_context = prior_context
    self.system_prompts = system_prompts
    self.tools = tools
    self.verbose = verbose
    self.conversation_history = ConversationHistoryEntryList(entries=[])
    self.max_plan_steps = max_plan_steps
    self.ascii_art = ascii_art
    
I.e. within an agency, the first agent divides the task up for the next agents,
and the final agent wraps everything up for the output desired from the agency.

Each agent between these is one of N choices based on the currently created
catalogue of agents. This will soon be custom designed.

It can be thought of as if each Agent is a specialized reflection engine, and the
first resource allocation agent will decide on the agents and tools.

However, the simplest way for now is to specify the agent structure and predetermine
all agent params. Let's do this first.
"""
import concurrent.futures
from typing import List
from literature_reviewer.agents.agent import Agent

class Agency:
    def __init__(
        self,
        name: str,
        task: str,
        agents: Agent | List[Agent | List[Agent]],
    ):
        self.name = name
        self.agents = agents
        
        self._validate_agent_structure()
        
    
    def run(self):
        results = []
        prior_context = ""
        for item in self.agents:
            if isinstance(item, Agent):
                item.prior_context = prior_context
                result = item.run(max_iterations=10)  # Assuming a default max_iterations
                results.append(result)
                prior_context += f"\n\nOutput from {item.name}:\n{result.final_output}"
            elif isinstance(item, list):
                parallel_results = []
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_to_agent = {executor.submit(self._run_agent, agent, prior_context): agent for agent in item}
                    for future in concurrent.futures.as_completed(future_to_agent):
                        agent = future_to_agent[future]
                        try:
                            result = future.result()
                            parallel_results.append(result)
                            prior_context += f"\n\nOutput from {agent.name}:\n{result.final_output}"
                        except Exception as exc:
                            print(f'{agent.name} generated an exception: {exc}')
                results.append(parallel_results)
        
        # Process and aggregate results as needed
        final_output = self._aggregate_results(results)
        return final_output

    def _run_agent(self, agent, prior_context):
        agent.prior_context = prior_context
        return agent.run(max_iterations=10)

    def _aggregate_results(self, results):
        # For now, just join all outputs
        aggregated_output = "\n\n".join([str(result) for result in results])
        return aggregated_output
    
        
    def _validate_agent_structure(self):
        if not isinstance(self.agents, list):
            self.agents = [self.agents]
        
        if not isinstance(self.agents[0], Agent) or not isinstance(self.agents[-1], Agent):
            raise ValueError("The first and last items in agents must be single Agents.")
        
        for i, item in enumerate(self.agents[1:-1], start=1):
            if not isinstance(item, (Agent, list)) or (isinstance(item, list) and not all(isinstance(sub_item, Agent) for sub_item in item)):
                raise ValueError(f"Item at index {i} must be either an Agent or a list of Agents.")
        

if __name__ == "__main__":
    import json
    from literature_reviewer.agents.components.model_call import ModelInterface
    from literature_reviewer.tools.basetool import BaseTool, ToolResponse

    from literature_reviewer.agents.components.agent_pydantic_models import *
    from dotenv import load_dotenv
    load_dotenv()
    from literature_reviewer.agents.components.frameworks_and_models import ( #noqa
        PromptFramework, Model
    )
    from literature_reviewer.agents.components.prompts.general_agent_system_prompts import (
        general_agent_planning_sys_prompt,
        general_agent_output_review_sys_prompt,
        general_agent_plan_revision_sys_prompt,
        general_agent_output_revision_sys_prompt,
    )
    from literature_reviewer.tools.basetool import BaseTool
    from literature_reviewer.agents.personas.squilliam_fancyson import (
        challenged_ascii_art
    )
    from literature_reviewer.agents.agent import Agent
    
    max_agent_iterations = 5
    
    agency_task = AgentTask(
        action="build an understanding of the growth modulating treatments for adolescent idiopathic scoliosis and the compuational modeling effots made in this area. report back on future research directions. Find and use appropriate reference material, then write an essay using it",
        desired_result="a short scientific overview of scoliosis treatment via growth modulation and associated compuational modeling techniques",
    )

    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini","OpenAI"),
    )
    
    # Example tools   
    class SearchTool(BaseTool):
        """
        A tool for searching academic literature and retrieving relevant papers.
        This tool interfaces with academic databases to find peer-reviewed articles
        based on given search queries. It's particularly useful for tasks that require
        finding supporting evidence, background information, or specific research in
        academic fields. The tool can handle complex search queries and return
        summaries or citations of relevant papers.
        """
        def __init__(self, model_interface: ModelInterface):
            super().__init__(
                name="SEARCHER",
                description="Searches for academic papers",
                model_interface=model_interface
            )

        def use(self, step: AgentPlanStep) -> str:
            system_prompt = "You are a helpful academic search assistant."
            user_prompt = f"Please search for relevant academic papers based on the following query: {step.prompt}. Output the papers to output and any required explanation to explanation"
            output = self.model_interface.chat_completion_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=ToolResponse,
            )
            return ToolResponse(**json.loads(output))

    class WriteTool(BaseTool):
        """
        A tool for writing creative poetry based on given prompts or themes.
        This tool utilizes natural language processing capabilities to generate
        original poems in various styles and formats. It can incorporate specific
        themes, emotions, or references provided in the prompt. The WriteTool is
        particularly useful for tasks that require creative writing, especially
        in poetic form, and can be used to create poems that reflect or incorporate
        academic concepts or findings when combined with other research tools.
        """
        def __init__(self, model_interface: ModelInterface):
            super().__init__(
                name="WRITER",
                description="Writes poetry",
                model_interface=model_interface
            )

        def use(self, step: AgentPlanStep) -> ToolResponse:
            system_prompt = "You are an author of many skills."
            user_prompt = f"Please write the type of content requested by the user based on the following prompt: {step.prompt}. Use the references provided, but only output the content itself as a single string in the output field, and if there are any citations or explanations necessary, fill those in the explanations field."
            output = self.model_interface.chat_completion_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=ToolResponse,
            )
            return ToolResponse(**json.loads(output))




    squilliam_tools = {
        "search": SearchTool(model_interface=model_interface),
        "write": WriteTool(model_interface=model_interface),
    }
    system_prompts = {
        "planning": general_agent_planning_sys_prompt,
        "review": general_agent_output_review_sys_prompt,
        "revise_plan": general_agent_plan_revision_sys_prompt,
        "revise_output": general_agent_output_revision_sys_prompt,
    }
    
    planner = Agent(
        name="Resource Allocator Steve",
        task=agency_task,
        prior_context="",
        model_interface=model_interface,
        system_prompts={
            "planning": lambda *args, **kwargs: "devise the best plan for the two worker agents (working on same task in parallel) in 3 or less steps for each agent. they will both receive the same plan",
            "review": lambda *args, **kwargs: "ensure your plan result is concise and captures the essence of the user task for the agency",
            "revise_plan": lambda *args, **kwargs: "revise the steps that led to this plan",
            "revise_output": lambda *args, **kwargs: "revise the output of the plan for correctness and clarity"
        },
        tools={"write": WriteTool(model_interface=model_interface)}, #<--makes up tools if none??????? TODO: check this out
        verbose=True,
        max_plan_steps=3,
        ascii_art = "HI :)"
    )
      
    worker = Agent(
        name="Squilliam Fancyson",
        task=agency_task,
        prior_context="",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools=squilliam_tools,
        verbose=True,
        max_plan_steps=3,
        ascii_art = challenged_ascii_art
    )
    
    aggregator = Agent(
        name="Output Aggregator Pichael",
        task=agency_task,
        prior_context="",
        model_interface=model_interface,
        system_prompts={
            "planning": lambda *args, **kwargs: "plan the best way to aggregate the result of the prior agents' work in 3 or less steps",
            "review": lambda *args, **kwargs: "ensure your aggregation result is concise and captures the result of the prior agents' work",
            "revise_plan": lambda *args, **kwargs: "revise the steps that led to this aggregation",
            "revise_output": lambda *args, **kwargs: "revise the output of the aggregation for correctness and clarity"
        },
        tools={"write": WriteTool(model_interface=model_interface)}, #<--makes up tools if none??????? TODO: check this out
        verbose=True,
        max_plan_steps=3,
        ascii_art = "AAAAGGGGGGGRRREEEEEGGGAAATTTEEEE"
    )
    
    agency_agents = [planner, [worker, worker], aggregator]
    
    agency = Agency(
        name="The Squids",
        agents=agency_agents,
        task=agency_task
    )
    
    print(agency.run())


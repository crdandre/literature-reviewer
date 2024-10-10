"""
https://github.com/brainqub3/jar3d_meta_expert/blob/main/main.py#L162

Trying to learn how to set up langgraph graphs in which to run custom agent architectures

Some ideas:
1. Meta-agent assembles a team of tools, agents or agencies depending on the task (i.e. any task or subtask can be handled by a tool, agent, or agency)
2. O1 maybe is well-suited to be the meta-agent and relay which tools can be arranged how
3. Before using a meta-agent, the user is the meta-agent. Start here.
"""








#nonsense
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START
from literature_reviewer.agents.agency import Agency
from literature_reviewer.agents.agent import Agent
from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.frameworks_and_models import PromptFramework, Model
from literature_reviewer.agents.components.prompts.general_agent_system_prompts import (
    general_agent_planning_sys_prompt,
    general_agent_output_review_sys_prompt,
    general_agent_plan_revision_sys_prompt,
    general_agent_output_revision_sys_prompt,
)
from literature_reviewer.agents.personas.squilliam_fancyson import challenged_ascii_art
from literature_reviewer.tools.examples.example_tools import WriteTool, SearchTool
from literature_reviewer.agents.components.agent_pydantic_models import AgentTask
import json

def create_state_typed_dict(agencies):
    """
    Creates a TypedDict 'State' where keys are agency names and values are List[str].
    """
    fields = {agency.name: List[str] for agency in agencies}
    return TypedDict('State', fields, total=False)

# Define the state structure
class AgencyState(TypedDict):
    messages: List[str]
    current_agency: str
    agencies: dict

# Create the graph
def create_agency_graph(agencies: List[Agency], agency_task: AgentTask) -> StateGraph:
    # Create the State subclass
    State = create_state_typed_dict(agencies)

    # Initialize the state
    state = State()

    # Register the agencies with the state
    for agency in agencies:
        agency.register(state)

    # Define the graph
    graph = StateGraph(State)

    # Dictionary to map agency names to node names
    agency_nodes = {}

    # Add nodes dynamically for each agency
    for agency in agencies:
        node_name = f"{agency.name}_node"
        agency_nodes[agency.name] = node_name
        graph.add_node(node_name, lambda state, agency=agency: agency.run(state=state))

    # Define the routing function
    def routing_function(state):
        if state.get("messages", []):
            last_message = state["messages"][-1]
            try:
                last_message_json = json.loads(last_message)
                next_agency = last_message_json.get("next_agency")
                next_agency_node = agency_nodes.get(next_agency, END)
            except json.JSONDecodeError:
                next_agency_node = END
        else:
            next_agency_node = agency_nodes[agencies[0].name]  # Start with the first agency
        return next_agency_node

    # Edge from START to first agency node
    graph.add_edge(START, agency_nodes[agencies[0].name])

    # Conditional edge from each agency node to next agency
    for agency in agencies:
        graph.add_conditional_edges(
            agency_nodes[agency.name],
            routing_function
        )

    return graph, state

# Initialize agents and agencies
def initialize_agencies():
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini", "OpenAI"),
    )

    agency_task = AgentTask(
        action="build an understanding of the growth modulating treatments for adolescent idiopathic scoliosis and the computational modeling efforts made in this area. report back on future research directions. Find and use appropriate reference material, then write an essay using it",
        desired_result="a short scientific overview of scoliosis treatment via growth modulation and associated computational modeling techniques",
    )

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
        tools={"write": WriteTool(model_interface=model_interface)},
        verbose=True,
        max_plan_steps=3,
        ascii_art="I AM STEVE :)"
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
        ascii_art=challenged_ascii_art
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
        tools={"write": WriteTool(model_interface=model_interface)},
        verbose=True,
        max_plan_steps=3,
        ascii_art="AAAAGGGGGGGRRREEEEEGGGAAATTTEEEE"
    )

    agency_agents = [planner, [worker, worker], aggregator]

    agency = Agency(
        name="The Squids",
        agents=agency_agents,
        task=agency_task
    )

    return [agency]

# Main execution
def main():
    agencies = initialize_agencies()
    agency_task = AgentTask(
        action="build an understanding of the growth modulating treatments for adolescent idiopathic scoliosis and the computational modeling efforts made in this area. report back on future research directions. Find and use appropriate reference material, then write an essay using it",
        desired_result="a short scientific overview of scoliosis treatment via growth modulation and associated computational modeling techniques",
    )
    graph, initial_state = create_agency_graph(agencies, agency_task)

    # Compile the workflow
    workflow = graph.compile()

    # Run the workflow
    for output in workflow.stream(initial_state):
        if output.get('final_output'):
            print("Final output:", output['final_output'])
            break

if __name__ == "__main__":
    main()


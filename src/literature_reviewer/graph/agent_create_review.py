"""
https://github.com/brainqub3/jar3d_meta_expert/blob/main/main.py#L162

Trying to learn how to set up langgraph graphs in which to run custom agent architectures

Some ideas:
1. Meta-agent assembles a team of tools, agents or agencies depending on the task (i.e. any task or subtask can be handled by a tool, agent, or agency)
2. O1 maybe is well-suited to be the meta-agent and relay which tools can be arranged how
3. Before using a meta-agent, the user is the meta-agent. Start here.
"""
from typing import TypedDict, List, Dict, Any
from pydantic import Field
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END, START
from literature_reviewer.agents.agent import Agent
from literature_reviewer.agents.agency import Agency
from literature_reviewer.tools.basetool import BaseTool
from datetime import datetime, timezone
import json

MAX_ITERATIONS = 3

def generate_triage_output_schema(agent_names: List[str]):
    return {name: str for name in agent_names if name != "Triage"}

def initialize_graph_state(nodes):
    fields = {node.name: List[Document] for node in nodes}
    return TypedDict('State', fields, total=False)

def build_graph(nodes):
    # Create the State using the initialize_graph_state function
    State = initialize_graph_state(nodes)
    state = State()
    
    # Initialize the graph with the State
    graph = StateGraph(State)

    # Dictionary to map node names to node functions
    node_functions = {}

    # Generate the dynamic schema for Triage output
    triage_output_schema = generate_triage_output_schema([node.name for node in nodes])

    # Generate the list of available agents once
    available_agents = [node.name for node in nodes if node.name != "Triage"]

    # Find the Triage agent and set its attributes
    triage_agent = next((node for node in nodes if node.name == "Triage"), None)
    if triage_agent:
        triage_agent.set_triage_attributes(available_agents, triage_output_schema)
    else:
        raise ValueError("Triage agent not found in the nodes list")

    # Add nodes dynamically for each node (Agency, Agent, or Tool)
    for node in nodes:
        node_name = f"{node.name}_node"
        if isinstance(node, (Agent, Agency, BaseTool)):
            def create_node_function(node):
                def node_function(state):
                    serialized_state = serialize_state(state)
                    result = node.run(max_iterations=MAX_ITERATIONS, state=json.dumps(serialized_state))
                    
                    # Update task for non-Triage agents based on Triage output
                    if node.name != "Triage" and state.get("Triage"):
                        triage_output = json.loads(state["Triage"][-1].page_content)
                        if node.name in triage_output:
                            node.task = triage_output[node.name]
                    
                    return {
                        node.name: state[node.name] + [Document(
                            page_content=json.dumps(result),
                            metadata={
                                "node_name": node.name,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        )]
                    }
                return node_function
            
            node_functions[node.name] = create_node_function(node)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
        
        graph.add_node(node_name, node_functions[node.name])

    # Identify the Triage agent
    triage_agent = next((node for node in nodes if node.name == "Triage"), None)
    if not triage_agent:
        raise ValueError("Triage agent not found in the nodes list")

    # Add edges
    graph.add_edge(START, f"{triage_agent.name}_node")
    for node in nodes:
        if node.name != "Triage":
            graph.add_edge(f"{triage_agent.name}_node", f"{node.name}_node")

    # Define the routing function
    def routing_function(state):
        # Check if all nodes have been executed
        if all(state.get(node.name) for node in nodes):
            return END
        # Find the next node that hasn't been executed yet
        for node in nodes:
            if not state.get(node.name):
                return f"{node.name}_node"
        # If all nodes have been executed, end the graph
        return END

    # Add conditional edges from all non-Triage nodes
    for node in nodes:
        if node.name != "Triage":
            graph.add_conditional_edges(
                f"{node.name}_node",
                routing_function
            )

    return graph, State


def serialize_document(doc):
    return {
        "metadata": doc.metadata,
        "page_content": doc.page_content
    }

def serialize_state(state):
    if isinstance(state, dict):
        return {k: serialize_state(v) for k, v in state.items()}
    elif isinstance(state, list):
        return [serialize_state(item) for item in state]
    elif hasattr(state, '__dict__'):
        return serialize_state(state.__dict__)
    else:
        return state

if __name__ == "__main__":
    from literature_reviewer.agents.components.model_call import ModelInterface
    from literature_reviewer.agents.components.frameworks_and_models import PromptFramework, Model
    from literature_reviewer.agents.components.prompts.general_agent_system_prompts import general_agent_system_prompts
    from literature_reviewer.agents.components.prompts.triage_agent_system_prompts import triage_agent_system_prompts

    # Create a simple model interface
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini", "OpenAI"),
    )
    
    context = "write a bit about tardigrades."
    MAX_PLAN_STEPS = 3
    
    # Create the Triage agent
    triage = Agent(
        name="Triage",
        task="Develop tasks for the Researcher and Writer agents based on the given context.",
        state=context,
        model_interface=model_interface,
        system_prompts=triage_agent_system_prompts,
        tools=None,
        verbose=True,
        max_plan_steps=MAX_PLAN_STEPS,
        ascii_art=None,
    )

    # Modify the researcher and writer agents to accept tasks from Triage
    researcher = Agent(
        name="Researcher",
        task="",
        state=context,
        model_interface=model_interface,
        system_prompts=general_agent_system_prompts,
        tools=None,
        verbose=True,
        max_plan_steps=MAX_PLAN_STEPS,
        ascii_art=None,
    )

    writer = Agent(
        name="Writer",
        task="",
        state=context,
        model_interface=model_interface,
        system_prompts=general_agent_system_prompts,
        tools=None,
        verbose=True,
        max_plan_steps=MAX_PLAN_STEPS,
        ascii_art=None,
    )

    nodes = [triage, researcher, writer]
    verbose = False

    graph, State = build_graph(nodes)
    workflow = graph.compile()

    initial_state = State(
        Triage=[],
        Researcher=[],
        Writer=[]
    )

    print("Starting graph execution...")

    # Execute the workflow and process each step
    for step in workflow.stream(initial_state):
        print(f"Step: {step}")
        # You can add more detailed logging or processing here

    print("Graph execution completed.")

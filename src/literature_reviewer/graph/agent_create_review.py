"""
https://github.com/brainqub3/jar3d_meta_expert/blob/main/main.py#L162

Trying to learn how to set up langgraph graphs in which to run custom agent architectures

Some ideas:
1. Meta-agent assembles a team of tools, agents or agencies depending on the task (i.e. any task or subtask can be handled by a tool, agent, or agency)
2. O1 maybe is well-suited to be the meta-agent and relay which tools can be arranged how
3. Before using a meta-agent, the user is the meta-agent. Start here.
"""

#nonsense
from typing import TypedDict, List, Callable
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END, START
from literature_reviewer.agents.agent import Agent
from literature_reviewer.agents.agency import Agency
from literature_reviewer.tools.basetool import BaseTool
from datetime import datetime, timezone
import json

def initialize_graph_state(nodes):
    fields = {node.name: List[Document] for node in nodes}
    return TypedDict('State', fields, total=False)

def build_graph(nodes, requirements):
    # Create the State using the initialize_graph_state function
    State = initialize_graph_state(nodes)

    # Initialize the graph with the State
    graph = StateGraph(State)

    # Dictionary to map node names to node functions
    node_functions = {}

    # Add nodes dynamically for each node (Agency, Agent, or Tool)
    for node in nodes:
        node_name = f"{node.name}_node"
        if isinstance(node, (Agent, Agency, BaseTool)):
            node_functions[node.name] = lambda state, node=node: {
                node.name: state[node.name] + [Document(
                    page_content=json.dumps(node.run(max_iterations=3)),
                    metadata={
                        "node_name": node.name,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )]
            }
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
        
        graph.add_node(node_name, node_functions[node.name])

    # Add edges
    graph.add_edge(START, f"{nodes[0].name}_node")
    for i in range(len(nodes) - 1):
        graph.add_edge(
            f"{nodes[i].name}_node",
            f"{nodes[i+1].name}_node",
            # lambda state: {
            #     'input_documents': state[nodes[i].name],
            #     'previous_node_metadata': state[nodes[i].name][-1].metadata if state[nodes[i].name] else {}
            # }
        )

    # Define the routing function
    def routing_function(state):
        # The last node in the sequence
        if state.get(nodes[-1].name):
            return END
        # Find the next node that hasn't been executed yet
        for node in nodes:
            if not state.get(node.name):
                return f"{node.name}_node"
        # If all nodes have been executed, end the graph
        return END

    # Add conditional edge from the last node
    graph.add_conditional_edges(
        f"{nodes[-1].name}_node",
        routing_function
    )

    return graph, State

# Add this new function
def print_state_update(state):
    print("\n--- State Update ---")
    if not state:
        print("State is empty")
    else:
        for node_name, documents in state.items():
            print(f"{node_name}:")
            if documents:
                for doc in documents:
                    try:
                        print(f"  Page Content: {doc.page_content}")
                        print(f"  Metadata: {doc.metadata}")
                    except:
                        print("DOC", doc)
            else:
                print("  No documents")
    print("--------------------\n")

if __name__ == "__main__":
    from literature_reviewer.agents.components.model_call import ModelInterface
    from literature_reviewer.agents.components.frameworks_and_models import PromptFramework, Model
    from literature_reviewer.agents.components.agent_pydantic_models import AgentTask
    from literature_reviewer.agents.components.prompts.general_agent_system_prompts import general_agent_system_prompts
    
    # Create a simple model interface
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini", "OpenAI"),
    )
    
    # Create agents
    researcher = Agent(
        name="Researcher",
        task=AgentTask(action="Research the given topic", desired_result="Comprehensive research findings"),
        prior_context="You are a diligent researcher tasked with gathering information.",
        model_interface=model_interface,
        system_prompts=general_agent_system_prompts,
        tools=None,
        verbose=True,
        max_plan_steps=5,
        ascii_art=None,
    )

    writer = Agent(
        name="Writer",
        task=AgentTask(action="Write a summary based on research", desired_result="Well-written summary"),
        prior_context="You are a skilled writer tasked with summarizing research findings.",
        model_interface=model_interface,
        system_prompts=general_agent_system_prompts,
        tools=None,
        verbose=True,
        max_plan_steps=5,
        ascii_art=None,
    )

    nodes = [researcher, writer]
    requirements = "write a bit about tardigrades."

    graph, State = build_graph(nodes, requirements)
    workflow = graph.compile()

    initial_state = State(
        Researcher=[],
        Writer=[]
    )

    print("Starting graph execution...")

    # Execute the workflow and get the final state
    for output in workflow.stream(initial_state):
        print_state_update(output)

    final_state = output

    print("\n--- Final State ---")
    for node_name, documents in final_state.items():
        print(f"{node_name}:")
        if documents:
            latest_doc = documents[-1]
            print(f"  Output: {latest_doc.page_content}")
            print(f"  Metadata: {latest_doc.metadata}")
        else:
            print("  No documents")
    print("--------------------\n")

    print("Graph execution completed.")

"""
https://github.com/brainqub3/jar3d_meta_expert/blob/main/main.py#L162

Trying to learn how to set up langgraph graphs in which to run custom agent architectures

Some ideas:
1. Meta-agent assembles a team of tools, agents or agencies depending on the task (i.e. any task or subtask can be handled by a tool, agent, or agency)
2. O1 maybe is well-suited to be the meta-agent and relay which tools can be arranged how
3. Before using a meta-agent, the user is the meta-agent. Start here.
"""
from typing import TypedDict, List
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END, START
from literature_reviewer.agents.agent import Agent
from literature_reviewer.agents.agency import Agency
from literature_reviewer.tools.basetool import BaseTool
import json
from literature_reviewer.tools.triage import AgentTaskList
from pydantic import ValidationError

MAX_ITERATIONS = 3
TRIAGE = "triage"

def generate_triage_output_schema(agent_names: List[str]):
    return {name: str for name in agent_names if name != TRIAGE}

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

    # Generate the list of available agents once
    available_agents = [node.name for node in nodes if node.name != TRIAGE]

    # Add nodes dynamically for each node (Agency, Agent, or Tool)
    for node in nodes:
        node_name = f"{node.name}_node"
        if isinstance(node, (Agent, Agency, BaseTool)):
            def create_node_function(node):
                def node_function(state):
                    serialized_state = serialize_state(state)
                    
                    # Update task for non-Triage agents based on Triage output
                    if node.name != TRIAGE and state.get(TRIAGE):
                        triage_output = json.loads(state[TRIAGE][-1].page_content)
                        try:
                            # Extract the task list from the final_output field
                            task_list_json = json.loads(triage_output['final_output'])
                            agent_task_list = AgentTaskList.model_validate(task_list_json)
                            for task in agent_task_list.tasks:
                                if task.node == node.name:
                                    node.task = task.task
                                    print(f"Assigning task to {node.name}: {task.task}")
                                    break
                            else:
                                print(f"No task found for {node.name}")
                        except (json.JSONDecodeError, ValidationError, KeyError) as e:
                            print(f"Error parsing Triage output: {e}")
                            print(f"Triage output: {triage_output}")
                            # Set a default task if parsing fails
                            node.task = f"Continue with the original task for {node.name}"
                    
                    result = node.run(max_iterations=MAX_ITERATIONS, state=json.dumps(serialized_state))
                    
                    return {
                        node.name: state.get(node.name, []) + [Document(
                            page_content=json.dumps(result),
                            metadata={
                                "node_name": node.name,
                            }
                        )]
                    }
                return node_function
            
            node_functions[node.name] = create_node_function(node)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
        
        graph.add_node(node_name, node_functions[node.name])

    # Identify the Triage agent
    triage_agent = next((node for node in nodes if node.name == TRIAGE), None)

    # Add edges
    graph.add_edge(START, f"{triage_agent.name}_node")
    for node in nodes:
        if node.name != TRIAGE:
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
        if node.name != TRIAGE:
            graph.add_conditional_edges(
                f"{node.name}_node",
                routing_function
            )

    return graph, State

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
    from literature_reviewer.tools.triage import TriageTool

    # Create a simple model interface
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini", "OpenAI"),
    )
    
    context = "write a dialogue between two tardigrades about their reflections on mortality. one page."
    MAX_AGENT_TASKS = 3
    MAX_PLAN_STEPS = 3
    VERBOSE = True
    available_agents=["Researcher", "Writer"]
    
    # Create the Triage agent
    # NOTE: this requires pre-knowledge of the agents ahead of time to specify available_agents
    triage_tool = TriageTool(
        model_interface=model_interface,
        available_agents=available_agents,
        user_goal=context,
        max_tasks=len(available_agents)
    )
    #basically trying to get this to do a tool call with refiection (one planning step)
    triage = Agent(
        name=TRIAGE,
        task="Generate a task list which assigns a task to each node to achieve the user's goal(s).",
        state=context,
        model_interface=model_interface,
        system_prompts=triage_agent_system_prompts,
        tools={"triage": triage_tool},
        verbose=VERBOSE,
        max_plan_steps=1,
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
        verbose=VERBOSE,
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
        verbose=VERBOSE,
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
        print("\n" + "=" * 22 + "STEP" + "=" * 24)
        for node, data in step.items():
            print(f"\033[1;33m{node}:\033[0m")
            for doc in data.get(node.split('_')[0], []):
                content = json.loads(doc.page_content)
                print(f"  \033[1;32mTask:\033[0m {content['task']}")
                print(f"  \033[1;32mIterations:\033[0m {content['iterations']}")
                print("  \033[1;32mFinal Plan:\033[0m")
                for plan_step in content['final_plan']:
                    print(f"    - {plan_step['step_name']}: {plan_step['action']}")
                print(f"  \033[1;32mFinal Output:\033[0m {content['final_output']}...")
                print(f"  \033[1;32mFinal Review:\033[0m {content['final_review']}")
        print("=" * 50)
        # You can add more detailed logging or processing here

    print("Graph execution completed.")

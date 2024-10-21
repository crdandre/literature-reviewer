"""
https://github.com/brainqub3/jar3d_meta_expert/blob/main/main.py#L162

Trying to learn how to set up langgraph graphs in which to run custom agent architectures

Some ideas:
1. Meta-agent assembles a team of tools, agents or agencies depending on the task (i.e. any task or subtask can be handled by a tool, agent, or agency)
2. O1 maybe is well-suited to be the meta-agent and relay which tools can be arranged how
3. Before using a meta-agent, the user is the meta-agent. Start here.


MONDAY TODO: Check that the state is properly updated and passed to each agent


"""
from typing import List, Dict, Union
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END, START
from literature_reviewer.agents.agent import Agent
from literature_reviewer.agents.agency import Agency
from literature_reviewer.tools.basetool import BaseTool
import json
from literature_reviewer.tools.triage import AgentTaskList, AgentTaskDict
from pydantic import BaseModel, Field

MAX_ITERATIONS = 3
TRIAGE = "Triage"

class GraphConfig(BaseModel):
    max_iterations: int = MAX_ITERATIONS
    verbose: bool = True

NodeType = Union[Agent, Agency, BaseTool]

class GraphState(BaseModel):
    task_list: List[Dict[str, str]] = Field(default_factory=list)
    node_outputs: Dict[str, List[Document]] = Field(default_factory=dict)
    completed_tasks: List[str] = Field(default_factory=list)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Document):
            return {
                "page_content": obj.page_content,
                "metadata": obj.metadata
            }
        return super().default(obj)

def create_node_function(node: NodeType, config: GraphConfig):
    def node_function(state: GraphState) -> Dict:
        if node.name not in state.node_outputs:
            state.node_outputs[node.name] = []

        result = None
        if node.name == TRIAGE:
            # Only run triage if task_list is empty
            if not state.task_list:
                result = node.run(max_iterations=config.max_iterations, state=json.dumps(state.model_dump(), cls=CustomJSONEncoder))
                try:
                    final_output = json.loads(result['final_output'])
                    state.task_list = final_output['tasks']
                except (KeyError, TypeError, json.JSONDecodeError) as e:
                    print(f"Error processing triage result: {e}")
                    state.task_list = []
        else:
            current_task = next((task for task in state.task_list if task['node'] == node.name and task['node'] not in state.completed_tasks), None)
            if current_task:
                node.task = current_task['task']
                node.context = f"Previous outputs: {json.dumps(state.node_outputs, cls=CustomJSONEncoder)}\nTask: {current_task['task']}"
                result = node.run(max_iterations=config.max_iterations, state=json.dumps(state.model_dump(), cls=CustomJSONEncoder))
                state.completed_tasks.append(node.name)
            else:
                print(f"No task found for {node.name}. Skipping.")

        if result:
            state.node_outputs[node.name].append(Document(page_content=json.dumps(result), metadata={"node_name": node.name}))
        else:
            print(f"No result generated for node {node.name}")

        return state.model_dump()
    
    return node_function

def build_graph(nodes: List[NodeType], config: GraphConfig):
    graph = StateGraph(GraphState)

    for node in nodes:
        graph.add_node(node.name, create_node_function(node, config))

    triage_agent = next(node for node in nodes if node.name == TRIAGE)

    graph.add_edge(START, triage_agent.name)

    def conditional_edge_func(state: GraphState):
        if not state.task_list:
            return END
        
        next_task = next((task for task in state.task_list if task['node'] not in state.completed_tasks), None)
        if next_task:
            next_node = next_task['node']
            return next_node
        else:
            return END

    # Connect triage to all other nodes and to END
    graph.add_conditional_edges(
        triage_agent.name,
        conditional_edge_func,
        {END: END, **{n.name: n.name for n in nodes if n.name != TRIAGE}}
    )

    # Connect all non-triage nodes back to triage and to END
    for node in nodes:
        if node.name != TRIAGE:
            graph.add_conditional_edges(
                node.name,
                conditional_edge_func,
                {END: END, **{n.name: n.name for n in nodes}}
            )

    return graph

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
    VERBOSE = False
    available_agents=["Researcher", "Writer"]
    
    # Create the Triage agent
    # NOTE: this requires pre-knowledge of the agents ahead of time to specify available_agents
    # TODO: this should include tool descriptions in available_agents in a dict and the model should be made aware of this
    triage_tool = TriageTool(
        model_interface=model_interface,
        available_agents=available_agents,
        user_goal=context,
        max_tasks=len(available_agents)
    )
    #basically trying to get this to do a tool call with refiection (one plan step)
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

    graph = build_graph(nodes, GraphConfig(verbose=verbose))
    workflow = graph.compile()

    initial_state = GraphState(node_outputs={node.name: [] for node in nodes})
    final_state = None

    print("Starting graph execution...")

    for step in workflow.stream(initial_state.model_dump()):
        print("\n" + "=" * 50)
        print(f"Current node: {list(step.keys())[0]}")
        state = GraphState(**step[list(step.keys())[0]])
        print("State:")
        print(f"  Task list: {[task['node'] for task in state.task_list]}")
        print(f"  Node outputs: {list(state.node_outputs.keys())}")
        print(f"  Completed tasks: {state.completed_tasks}")

        final_state = state  # Update the final_state with each step

    print("\nGraph execution completed.")
    print("\n"+"="*50)
    print("\nFinal State:")
    print(json.dumps(serialize_state(final_state), indent=2))
    print("\n"+"="*50)
    
    writer_output = final_state.node_outputs.get('Writer', [])
    if writer_output:
        writer_content = json.loads(writer_output[-1].page_content)
        print(f"Final Output:\n{writer_content['final_output']}")
    else:
        print("No output from Writer node found.")




# Add this function at the end of the file
def serialize_state(state):
    if isinstance(state, dict):
        return {k: serialize_state(v) for k, v in state.items()}
    elif isinstance(state, list):
        return [serialize_state(item) for item in state]
    elif hasattr(state, '__dict__'):
        return serialize_state(state.__dict__)
    else:
        return state

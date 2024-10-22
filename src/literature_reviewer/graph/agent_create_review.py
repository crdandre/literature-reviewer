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
                
                #TODO: make things like this more generic
                # This feeds the output of the query generation to the tool for corpus gathering
                if node.name == "LiteratureSearcher" and "SearchQueryGenerator" in state.node_outputs:
                    search_queries_json = state.node_outputs["SearchQueryGenerator"][-1].page_content
                    search_queries_data = json.loads(search_queries_json)
                    output_json = json.loads(search_queries_data.get('final_output', '{}'))
                    search_queries = output_json.get('queries', [])
                    node.tools["corpus_gatherer"].search_queries = search_queries

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
    from literature_reviewer.agents.components.prompts.research_query_generator_agent_system_prompts import research_query_generator_agent_system_prompts
    from literature_reviewer.agents.components.prompts.literature_search_agent_system_prompts import literature_search_agent_system_prompts
    from literature_reviewer.tools.triage import TriageTool
    from literature_reviewer.tools.research_query_generator import ResearchQueryGenerator
    from literature_reviewer.tools.corpus_gatherer import CorpusGatherer

    # Create a simple model interface
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o", "OpenAI"),
    )
    
    goal = "write a short summary of the research articles you find on computational modeling in scoliosis surgery. use the ResearchQueryGenerator tool when creating queries"
    
    user_supplied_pdfs_directory = "/home/christian/literature-reviewer/user_inputs/user_supplied_pdfs"
    num_vec_db_queries = 3
    vec_db_query_num_results = 2
    num_s2_queries = 2
    
    pdf_download_path = "/home/christian/literature-reviewer/test_outputs/downloaded_pdfs"
    vector_db_path = "/home/christian/literature-reviewer/test_outputs/chroma_db"
    
    MAX_AGENT_TASKS = 3
    MAX_PLAN_STEPS = 3
    VERBOSE = True
    available_agents=["SearchQueryGenerator", "LiteratureSearcher", "Writer"]
    
    # Create the Triage agent
    # NOTE: this requires pre-knowledge of the agents ahead of time to specify available_agents
    # TODO: this should include tool descriptions in available_agents in a dict and the model should be made aware of this
    #basically trying to get this to do a tool call with refiection (one plan step)
    triage = Agent(
        name=TRIAGE,
        task="Generate a task list which assigns a task to each node to achieve the user's goal(s).",
        state=goal,
        model_interface=model_interface,
        system_prompts=triage_agent_system_prompts,
        tools={
            "triage": TriageTool(
                model_interface=model_interface,
                available_agents=available_agents,
                user_goal=goal,
                max_tasks=len(available_agents)
            )
        },
        verbose=VERBOSE,
        max_plan_steps=1,
        ascii_art=None,
    )

    search_query_generator = Agent(
        name="SearchQueryGenerator",
        task="",
        state="",
        model_interface=model_interface,
        system_prompts=research_query_generator_agent_system_prompts,
        tools={
            "research_query_generator": ResearchQueryGenerator(
                user_goals_text=goal,
                user_supplied_pdfs_directory=user_supplied_pdfs_directory,
                model_interface=model_interface,
                num_vec_db_queries=num_vec_db_queries,
                vec_db_query_num_results=vec_db_query_num_results,
                num_s2_queries=num_s2_queries,
            ),  
        },
        verbose=VERBOSE,
        max_plan_steps=1,
        ascii_art=None,
    )
    
    literature_searcher = Agent(
        name="LiteratureSearcher",
        task="",
        state="",
        model_interface=model_interface,
        system_prompts=literature_search_agent_system_prompts,
        tools={
            "corpus_gatherer": CorpusGatherer(
                search_queries=None,  # This will be updated dynamically
                user_goals_text=goal,
                model_interface=model_interface,
                pdf_download_path=pdf_download_path,
                chromadb_path=vector_db_path,
            ),
        },
        verbose=VERBOSE,
        max_plan_steps=1,
        ascii_art=None,
    )

    writer = Agent(
        name="Writer",
        task="",
        state="",
        model_interface=model_interface,
        system_prompts=general_agent_system_prompts,
        tools=None,
        verbose=VERBOSE,
        max_plan_steps=MAX_PLAN_STEPS,
        ascii_art=None,
    )

    nodes = [triage, search_query_generator, literature_searcher, writer]
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

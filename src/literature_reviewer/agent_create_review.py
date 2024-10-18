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
from langgraph.graph import StateGraph, END

from literature_reviewer.agents.agent import Agent
from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.frameworks_and_models import PromptFramework, Model
from literature_reviewer.agents.components.agent_pydantic_models import AgentTask
from literature_reviewer.tools.examples.example_tools import WriteTool, SearchTool
from literature_reviewer.agents.components.prompts.general_agent_system_prompts import (
    general_agent_planning_sys_prompt,
    general_agent_output_review_sys_prompt,
    general_agent_plan_revision_sys_prompt,
    general_agent_output_revision_sys_prompt,
)

# Define the state structure
class State(TypedDict):
    messages: List[str]
    current_agent: str

def create_agent_graph():
    # Initialize the graph
    graph = StateGraph(State)

    # Create a simple model interface
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini", "OpenAI"),
    )

    # Define system prompts
    system_prompts = {
        "planning": general_agent_planning_sys_prompt,
        "review": general_agent_output_review_sys_prompt,
        "revise_plan": general_agent_plan_revision_sys_prompt,
        "revise_output": general_agent_output_revision_sys_prompt,
    }

    # Create agents
    researcher = Agent(
        name="Researcher",
        task=AgentTask(action="Research the given topic", desired_result="Comprehensive research findings"),
        prior_context="You are a diligent researcher tasked with gathering information.",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools={"search": SearchTool(model_interface=model_interface)},
        verbose=True,
        max_plan_steps=5,
        ascii_art=None,
    )

    writer = Agent(
        name="Writer",
        task=AgentTask(action="Write a summary based on research", desired_result="Well-written summary"),
        prior_context="You are a skilled writer tasked with summarizing research findings.",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools={"write": WriteTool(model_interface=model_interface)},
        verbose=True,
        max_plan_steps=5,
        ascii_art=None,
    )

    # Add nodes for each agent
    graph.add_node("research", lambda state: researcher.run(max_iterations=3))
    graph.add_node("write", lambda state: writer.run(max_iterations=3))

    # Define the routing function
    def router(state):
        if state["current_agent"] == "Researcher":
            return "write"
        elif state["current_agent"] == "Writer":
            return END
        else:
            return "research"

    # Add edges
    graph.add_edge("research", "write")
    graph.add_edge("write", END)

    # Set the entry point
    graph.set_entry_point("research")

    return graph

def main():
    graph = create_agent_graph()
    workflow = graph.compile()

    initial_state = State(
        messages=[],
        current_agent="Researcher"
    )

    for output in workflow.stream(initial_state):
        if output['current_agent'] == END:
            print("Final output:", output['messages'][-1])
            break

if __name__ == "__main__":
    main()

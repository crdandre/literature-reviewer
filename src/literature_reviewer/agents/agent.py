"""
Agent class

Includes model calling, tool definition if necessary,
reflection, at agent level

In order to reflect, there is Agent-internal planning, 
execution, review, and if needed revision

This simulates CoT-ish behavior. Alternatively calls to o1
will have to be handled differently...
--> could have an Agent class which could beciome Agent
or O1Agent depending on inputs


Additions:
1. [x] Better printout
2. [ ] Requiring sources/citations baked into classes as option
3. [ ] Efficient use of prior context, rather than pure accumulation?

Constraints:
1. [~] Tools are responsible for their own output formats which 
       adhere to ToolResponse but can extend it
"""
import json, logging, sys
from datetime import datetime, timezone
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.agent_pydantic_models import (
    AgentPlan,
    AgentPlanStep,
    AgentPlanStep,
    AgentPlan,
    PlanStepResult,
    PlanStepResultList,
    AgentReviewVerdict,
    AgentTask,
    AgentProcessOutput,
    AgentRevisionTask,
    AgentOutputRevision,
    ConversationHistoryEntry,
    ConversationHistoryEntryList
)
from literature_reviewer.agents.components.memory import (
    LoadingAnimation, run_with_loading, add_to_conversation_history
)
from literature_reviewer.agents.components.printout import print_ascii_art
from literature_reviewer.tools.basetool import BaseTool, ToolResponse


class Agent:
    """
    An intelligent agent capable of planning and executing tasks.

    Attributes:
        name (str): The name of the agent.
        task (AgentTask): The task assigned to the agent.
        prior_context (str): Any prior context or information given to the agent.
        model_interface (ModelInterface): The interface for interacting with the language model.
        system_prompts (dict): A dictionary of system prompts for different agent functions.
                               Contains "planning", "action", "review", and "revision" prompts.
        tools (Dict[str, BaseTool]): A dictionary of tools available to the agent.
        verbose (bool): Whether to enable verbose logging.
        conversation_history (ConversationHistoryEntryList): A list of conversation history entries.
        max_plan_steps (int): The maximum number of steps allowed in a plan.
        logger (logging.Logger): The logger object for this agent.

    Args:
        name (str): The name of the agent.
        task (AgentTask): The task assigned to the agent.
        prior_context (str): Any prior context or information given to the agent.
        model_interface (ModelInterface): The interface for interacting with the language model.
        system_prompts (dict): A dictionary of system prompts for different agent functions.
                               Must include "planning", "action", "review", and "revision" prompts.
        tools (Dict[str, BaseTool]): A dictionary of tools available to the agent.
        verbose (bool): Whether to enable verbose logging.
        max_plan_steps (int, optional): The maximum number of steps allowed in a plan. Defaults to 10.
    """
    def __init__(
        self,
        name: str,
        task: AgentTask,
        prior_context: str,
        model_interface: ModelInterface,
        system_prompts,
        tools: Dict[str, BaseTool],
        verbose,
        max_plan_steps=10,
        ascii_art=None,
    ):
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
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.name}")
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        self.loading_animation = LoadingAnimation()
        
        if self.prior_context:
            self.conversation_history.entries.append(ConversationHistoryEntry(
                agent_name=self.name,
                heading="Prior Context",
                timestamp=datetime.now(timezone.utc).isoformat(),
                model=self.model_interface.model.model_name,
                content=self.prior_context,
                content_structure="str"
            ))
            self.logger.debug(f"Added prior context: {self.prior_context}")


    @run_with_loading
    @add_to_conversation_history
    def create_plan(self):
        """
        Gets agent-specific prompt for creating a step-by-step plan
        to accomplish the task within agent scope
        """
        self.logger.debug("Starting planning process")
        
        tool_specs = {name: tool.__doc__ for name, tool in self.tools.items()} if self.tools else None
        
        plan_json = self.model_interface.chat_completion_call(
            system_prompt=self.system_prompts.get("planning")(
                max_steps=self.max_plan_steps,
                tool_specs=tool_specs
            ),
            user_prompt=self.task.as_xml_string(),
            response_format=AgentPlan,
        )
                
        return AgentPlan(**json.loads(plan_json))

        
    @run_with_loading
    @add_to_conversation_history    
    def enact_plan(self, plan):
        """
        Enacts the plan created in create_plan
        Uses tools described in tool_spec if helpful to enacting the plan
        
        Takes each step of the plan, reads the tool used,
        routes to the appropriate tool for that step
        """
        results = PlanStepResultList(plan_steps=[])
        accumulated_context = ""
        for step in plan.steps:
            # Add accumulated context to the step prompt
            step_prompt = f"{accumulated_context}\n\nCurrent step: {step.prompt}"
            
            if step.tool_name is None or step.tool_name not in self.tools:
                # Handle steps without a tool or with an unknown tool
                result_json = self.model_interface.chat_completion_call(
                    system_prompt="You are a helpful assistant executing a task. Provide the result and a brief explanation.",
                    user_prompt=f"{step_prompt}\n\nRespond in ToolResponse format with 'output' and 'explanation' fields.",
                    response_format=ToolResponse
                )
                output = ToolResponse(**json.loads(result_json))
            else:
                try:
                    # Pass the updated prompt with accumulated context to the tool
                    step.prompt = step_prompt
                    output = self.tools[step.tool_name].use(step)
                except Exception as e:
                    self.logger.error(f"Error executing step '{step}' with tool '{step.tool_name}': {str(e)}")
                    continue
            
            step_result = PlanStepResult(plan_step=step, result=output)
            results.plan_steps.append(step_result)
            
            # Update accumulated context with the result of this step
            accumulated_context += f"\nStep {len(results.plan_steps)} result: {output.output}"
            
            self.logger.info(f"Executed step: {step}")
            self.logger.debug(f"Step result: {output}")
        
        return results


    @run_with_loading
    @add_to_conversation_history
    def review_output(self, output):
        """
        Reviews the output of the plan execution.
        
        Given an agent-specific (or general) review system prompt,
        The user prompt here can be generic and supply the material
        to be reviewed.
        """
        self.logger.debug("Starting review process")
        
        review_prompt = f"""
        Task: {self.task.as_xml_string()}
        
        Output to review:
        {output}
        
        Please review the output and determine if it successfully completes the task.
        Provide detailed feedback, including strengths and areas for improvement.
        """
        
        review_result = self.model_interface.chat_completion_call(
            system_prompt=self.system_prompts.get("review")(),
            user_prompt=review_prompt,
            response_format=AgentReviewVerdict
        )
        
        return AgentReviewVerdict(**json.loads(review_result))


    @run_with_loading
    @add_to_conversation_history
    def revise_plan(self, plan, feedback):
        """
        Revises the plan based on the review feedback.
        """
        self.logger.debug("Starting plan revision process")
        
        revision_prompt = f"""
        Original Task: {self.task.as_xml_string()}
        
        Original Plan:
        {plan.as_formatted_text()}
        
        Review Feedback:
        {feedback}
        
        Please revise the plan based on the feedback provided. Ensure the revised plan addresses the issues raised in the feedback.
        """
        
        revised_plan_json = self.model_interface.chat_completion_call(
            system_prompt=self.system_prompts.get("revise_plan")(plan),
            user_prompt=revision_prompt,
            response_format=AgentPlan,
        )
        
        return AgentPlan(**json.loads(revised_plan_json))
    
    
    @run_with_loading
    @add_to_conversation_history
    def revise_output(self, output, feedback):
        """
        Revises the output based on the review feedback.
        For minor edits like style, clarity, etc. rather than
        errors that stem from the concepts in the task list
        """
        self.logger.debug("Starting output revision process")
        
        revision_prompt = f"""
        Original Task: {self.task.as_xml_string()}
        
        Original Output:
        {output}
        
        Review Feedback:
        {feedback}
        
        Please revise the output based on the feedback provided. Ensure the revised output addresses the issues raised in the feedback and better fulfills the original task.
        """
        
        revised_output_json = self.model_interface.chat_completion_call(
            system_prompt=self.system_prompts.get("revise_output")(output),
            user_prompt=revision_prompt,
            response_format=AgentOutputRevision,
        )
        
        return AgentOutputRevision(**json.loads(revised_output_json))


    @add_to_conversation_history
    def run(self, max_iterations):
        print_ascii_art(self.ascii_art)
        
        iteration = 0
        plan = self.create_plan()
        output = None
        final_result = None
        final_review = None
        
        try:
            while iteration < max_iterations:
                iteration += 1
                
                if output is None:
                    output = self.enact_plan(plan)
                
                review_result = self.review_output(output)
                
                if review_result.verdict:
                    self.logger.info("Task completed successfully")
                    final_result = output
                    final_review = f"{'Passed' if review_result.verdict else 'Failed'}"
                    break
                else:
                    self.logger.info(f"Review failed. Recommendation: {review_result.recommendation}")
                    if iteration < max_iterations:
                        if review_result.revision_location == "plan":
                            plan = self.revise_plan(plan, review_result.recommendation)
                            output = None  # Reset output to force re-execution of the plan
                        elif review_result.revision_location == "output":
                            revision_result = self.revise_output(output, review_result.recommendation)
                            output = revision_result.revised_output
                        else:
                            self.logger.warning(f"Unknown revision location: {review_result.revision_location}")
                    else:
                        self.logger.warning("Max iterations reached without success")
                        final_result = output
                        final_review = f"Max iterations reached without success:\n\n{review_result.recommendation}"
            
            final_output = self._extract_final_output(final_result)
            
            return AgentProcessOutput(
                task=self.task,
                iterations=iteration,
                final_plan=plan.as_formatted_text(),
                final_output=final_output,
                final_review=final_review
            )
        finally:
            self.loading_animation.stop()
            sys.stdout.write('\rDone!     \n')
            sys.stdout.flush()


    def _extract_final_output(self, output):
        if isinstance(output, PlanStepResultList) and output.plan_steps:
            last_step = output.plan_steps[-1]
            return str(last_step.result.output)
        elif isinstance(output, str):
            return output
        return "No output generated"
    
    
        
if __name__ == "__main__":
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
        challenged_ascii_art,
        complete_ascii_art
    )
    from literature_reviewer.tools.research_query_generator import ResearchQueryGenerator

    agent_task = AgentTask(
        action="Plan to write a short scientific summary of the literature on computational spine modeling in scoliosis. Search for the appropriate search queries, summarize them, then write up a list of the queries followed by a paragraph explaining why you would like to search for these queries",
        desired_result="a list of queries and an explanation for them",
    )

    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini","OpenAI"),
    )

    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt_ais.txt", "r") as file:
        user_goals_text = file.read()
    user_supplied_pdfs_directory = "/home/christian/literature-reviewer/user_inputs/user_supplied_pdfs"
    num_vec_db_queries = 3
    vec_db_query_num_results = 2
    num_s2_queries = 10

    
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


    tools = {
        "search": SearchTool(model_interface=model_interface),
        "write": WriteTool(model_interface=model_interface),
        "generate_queries": ResearchQueryGenerator(
            user_goals_text=user_goals_text,
            user_supplied_pdfs_directory=user_supplied_pdfs_directory,
            model_interface=model_interface,
            num_vec_db_queries=num_vec_db_queries,
            vec_db_query_num_results=vec_db_query_num_results,
            num_s2_queries=num_s2_queries,
        ),
    }
    
    system_prompts = {
        "planning": general_agent_planning_sys_prompt,
        "review": general_agent_output_review_sys_prompt,
        "revise_plan": general_agent_plan_revision_sys_prompt,
        "revise_output": general_agent_output_revision_sys_prompt,
    }
      
    agent = Agent(
        name="Squilliam Fancyson",
        task=agent_task,
        prior_context="",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools=tools,
        verbose=True,
        max_plan_steps=10,
        ascii_art = challenged_ascii_art
    )
    

    
    result = agent.run(max_iterations=10)

    print_ascii_art(ascii_art=complete_ascii_art)
    
    console = Console(file=sys.stderr)
    output_text = Text(result.final_output)
    output_panel = Panel(output_text, title="Final Output", border_style="bold cyan", expand=False)
    console.print(output_panel)
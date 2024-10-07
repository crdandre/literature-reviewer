"""
Agent class
Includes model calling, tool definition if necessary,
reflection, at agent level

In order to reflect, there is Agent-internal planning, 
execution, review, and if needed revision

This simulates CoT-ish behavior. Alternatively calls to o1
will have to be handled differently...
--> could have an Agent class which could beciome LLMAgent
or O1Agent depending on inputs


Additions:
1. [ ] Better printout
2. [ ] Requiring sources/citations baked into classes as option
3. [ ] Efficient use of prior context, rather than pure accumulation?

Constraints:
1. [ ] Tools are responsible for their own output formats which 
       adhere to ToolResponse but can extend it
"""


import datetime, json, logging, sys
from pydantic import BaseModel
from typing import Dict
from literature_reviewer.agents.model_call import ModelInterface
from literature_reviewer.components.tool import BaseTool, ToolResponse
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from literature_reviewer.agents.agent_pydantic_models import *

"""
=======================================================
Agents
=======================================================
"""
class LLMAgent:
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


    #decorator function for the others
    def add_to_conversation_history(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            heading = func.__name__
            timestamp = datetime.now(timezone.utc).isoformat()
            
            content_structure = ""
            if isinstance(result, BaseModel):
                content_structure = result.__class__.__name__
                content = result.model_dump_json()
            else:
                content = str(result)
            
            entry = ConversationHistoryEntry(
                agent_name=self.name,
                heading=heading,
                timestamp=timestamp,
                model=self.model_interface.model.model_name,
                content=content,
                content_structure=content_structure
            )
            self.conversation_history.entries.append(entry)
            
            if self.verbose:
                self.print_latest_entry(entry)
            
            return result
        return wrapper


    def print_ascii_art(self, ascii_art=None):
        art_to_print = ascii_art if ascii_art is not None else self.ascii_art
        console = Console()
        if art_to_print:
            # Convert the ASCII art to a Text object and style it
            colored_art = Text(art_to_print)
            colored_art.stylize("cyan")
            console.print(colored_art)

    def print_latest_entry(self, entry):
        console = Console(file=sys.stderr)
        
        # Combine all entry details into the panel title
        title = f"{entry.agent_name} - {entry.heading} | {entry.timestamp} | {entry.model}"
        
        # Create the content
        if entry.content_structure:
            try:
                model_class = globals()[entry.content_structure]
                parsed_content = model_class.parse_raw(entry.content)
                content = parsed_content.as_rich()
            except (KeyError, ValueError) as e:
                content = Text(f"Error formatting content: {str(e)}", style="red")
        else:
            content = Markdown(entry.content)
        
        # Create the main panel with the content
        main_panel = Panel(
            content,
            title=title,
            border_style="blue",
            padding=(1, 1)
        )
        
        console.print(main_panel)
        console.print()


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


    @add_to_conversation_history
    def review_output(self, output):
        """
        Reviews the output of the plan execution.
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
        self.print_ascii_art(self.ascii_art)  # Print ASCII art at the beginning of the run
        
        iteration = 0
        
        plan = self.create_plan()
        output = None
        final_result = None
        final_review = None
        
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"Starting iteration {iteration}")
            
            if output is None:
                output = self.enact_plan(plan)
            
            review_result = self.review_output(output)
            
            # Print the review verdict
            self.logger.info(f"Review verdict: {'Passed' if review_result.verdict else 'Failed'}")
            
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
    from literature_reviewer.agents.frameworks_and_models import ( #noqa
        PromptFramework, Model
    )
    from literature_reviewer.components.prompts.agent import (
        general_agent_planning_sys_prompt,
        general_agent_output_review_sys_prompt,
        general_agent_plan_revision_sys_prompt,
        general_agent_output_revision_sys_prompt,
    )
    from literature_reviewer.components.tool import BaseTool

    agent_task = AgentTask(
        action="Create a short historical essay written like shakespeare. Find and use appropriate reference material, then write the essay using it",
        desired_result="a short historical essay written like shakespeare",
    )
    # agent_task = AgentTask(
    #     action="Create a poem backed by concepts discussed by famous scientists, mention their scholarly work, get one or two exact citations to mention in-text. First, gather ideas, second, find the key themes, third, write the poem",
    #     desired_result="A poem backed by concepts discussed by famous scientists",
    # )
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
            system_prompt = "You are a creative poetry writer."
            user_prompt = f"Please write a poem based on the following prompt: {step.prompt}. Use the references provided, but only output the poem itself as a single string in the output field, and if there are any citations or explanations necessary, fill those in the explanations field."
            output = self.model_interface.chat_completion_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=ToolResponse,
            )
            return ToolResponse(**json.loads(output))


    tools = {
        "search": SearchTool(model_interface=model_interface),
        "write": WriteTool(model_interface=model_interface),
    }
    
    system_prompts = {
        "planning": general_agent_planning_sys_prompt,
        "review": general_agent_output_review_sys_prompt,
        "revise_plan": general_agent_plan_revision_sys_prompt,
        "revise_output": general_agent_output_revision_sys_prompt,
    }
    
    # Add a placeholder for custom ASCII art
    challenged_ascii_art = """
    
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ()               _  _               
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   /\              // //               
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  /  )  _,  . . o // // o __.  ______  
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒█▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓█▓▒░░░░░░░░░░░░░░░░░░░░░░ /__/__(_)_(_/_<_</_</_<_(_/|_/ / / <_ 
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒▒▒▓███▓░░░░░░░░░░░░░░░░░        />                             
░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓██▓░░░░░░░░░░░░░░       |/                              
░░░░░░░░░░░░░░░░░░░░░░░░░▒█▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓█▒░░░░░░░░░░░    _____                              
░░░░░░░░░░░░░░░░░░░░░░░░▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▒█▓░░░░░░░░░     /  '                              
░░░░░░░░░░░░░░░░░░░░░░░█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░░▒░▒▒▒▒▒▒▒▒▓█▓░░░░░░░  ,-/-,__.  ____  _. __  , _   __ ____ 
░░░░░░░░░░░░░░░░░░░░░▒█▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░▒▓█▓▓░░░░░░░░░░▒▒▒▒▒▒▒▒█▓░░░░░ (_/  (_/|_/ / <_(__/ (_/_/_)_(_)/ / <_
░░░░░░░░░░░░░░░░░░░░░█▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░▒▒▓▓▒▒▒▒░░░░░░░░░░░░░░░░░░░▒▒▒██░░░░                       /               
░░░░░░░░░░░░░░░░░░░░▓▒▒▒▒▒▒▒▒▒░░░▒▒▓▒▒▒▒▒▒▓▓▒▒▒▒▒▒▓▓▓▓▓▓▒▒▒░░░░░░░░░░░░░░▒░░▓█░░░                      '                
░░░░░░░░░░░░░░░░░░░▒█▒▒▒▒▒▒▒░░▒▒▒░░░░░░░▒▒▒▒▓▓▓▒▒░░░░░░░░▒▒▒░░░░░░░░░░░░░░░░░█░░░
░░░░░░░░░░░░░░░░░░░██▒▒▒▒▒▒░░░░░▒▓▓▓▓▓▓▓▒▒░▒▒▒▒▒▓▓▓▓▓▓▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░█▒░░
░░░░░░░░░░░░░░░░░░░██▒▒▒▒▒░░░░░░▒▒░░░░░▒▓██████████▓▓▓▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░█▓░░
░░░░░░░░░░░░░░░░░░░▓█▒▒▒▒░░░░░░▒▒▓██████████▓▒▒▒▒▒█▓░░░░░░░░░░░░░░░░░░░░░░░░░██░░
░░░░░░░░░░░░░░░░░░░░█▓░░░░░░░░░░░▓▓▓▒▒▒██▒▒▒▒▒▒▒▒▒▒█▒░░░░░░░░░░░░░░░░░░░░░░░░█░░░
░░░░░░░░░░░░░░░░░░░░░█▒░░░░░░░░░▓▓▒▒▒▒▒█▓▒▒▒▒▒▒▒▒▒▒▒▓░▒▒░░░░░░░░░░░░░░░░░░░░▓▓░░░
░░░░░░░░░░░░░░░░░░░░░▒█▒▒░░░░░░▓█▒▒▒▒▒▒█▒▒▒▒▒▒▒▒▒▒▒▒█▒░░▒░░░░░░░░░░░░░░░░░░▓█░░░░
░░░░░░░░░░░░░░░░░░░░░░░█▓▒░░░░░█▓▒▒▒▒▒▓█▓▒▒▒▒▒▒▒▒▒▒▒▓▓░░░░░░░░░░░░░░░░░░░░▓█▒░░░░
░░░░░░░░░░░░░░░░░░░░░░░░▒██▒░░░█▓▒▒▒▒▒▓█▓▒▒▒▒▒▒▒▒▒▒▒▓█░░░░░░░░░░░░░░░░░░░██░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▒▒█▓▓▒▒▒▒▓█▒▒▒▒▒▒▒▒▒▒▓▒▓▓█▒░░░░░░░░░░░░░░░▓█▒░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█▒▒▒▒▓██▓▒▒▒▒▒▒████▒▒▓▒▒░░░░░░░░░░░░░▒▓█▓░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▒░░░▒███░░░░░░█▓▓█░░█▒░░░░░░░░░░░▒▓▓▒░░░░░░░░░░░░
░░░░░░░░░░▓█▓▓▓▓▓▓▒░░░░░░░░░░░░░▓░░░░▒▓▓▓░░░░░▒▓▓▒░▒▓░░░▒░▒▒▒▒▒▒▓▒░░░░░░░░░░░░░░░
░░░░░░░░▓█▓▒▒▒▒▒▒▒▓█▓░░░░░░░░░░░░▓▒░░▓▒▒▒▓░░░░░░░░▒█▒░░▒▒▒█▒░░░░░░░░░░░░░░░░░░░░░
░░░░░░░▓█▒▒▒▒▒░░░▒░░▓▓░░░░░░░░░░░░░▒█▒▒▒▒▒█▒░░░░▒█▒░░░▒▒▒▒█░░░░░░░░░░░░░░░░░░░░░░
░░░░░░▓█▒▒▒▒░░▒░░░▒░░▓█░░░░░░░░░░░░▒▓▒▒▒▒▒▒█▓▒▓▒▒▒░░░▒▒▒▒░█░░░░░░░░░░░░░░░░░░░░░░
░░░░░▓█▒▒▒▒▒░░▒░░░░░░░█▓░░░░░░░▒▓▓▓▓▒▒▒▒▒▒█▒▒░░░░░░░▒▒▒▒▒▒▓▓▓▓▒░░░░░░░░░░░░░░░░░░
░░░░░█▓▒▒▒▒▒░▒░░░▒█▓▒░▓█░░░▒▓▓▒▒▒▒█▒▒▒▒▒▒▓▓▒▒░░░░░░░░░░░░░░░▒▒▓▓█▓▒▒░░░░░░░░░░░░░ 
░░░░█▓▒▒▒▒░░▒░░▒▓█▓▒▒░▓█░▒▓▒░░░░░█▒▒▒▒▒▒▒█▓▒▒▒▒▒▒▒▒▒▒▒▒░░░░▒░▒░▒░▒▓▓█▓░░░░░░░░░░░
░░░▒█▒▒▒░░░░░▒▓█▓▒▒▒░░▓▓█▒░░░▒░░▓▒▒▒▒▒▒▒░██▓▓▒▒▒▒▒▒▒▒▒▓▓█▓▒▒▒▒▒▒░▒▒░░▒▓█▒░░░░░░░░
░░░▓▓▒▒░░▒▓██████▓▒▒░░██▒░░░░░░▒█▒▒▒▒▒▒▒▒▒████████▓▓▓▓▓▓▓▓▓▓▓▓▓██▓▒░▒░░▒█░░░░░░░░
░░░░░░░▒░▒█▓▒▒▒▒▒█▒▒░░█▓▓░░░░░░▒█▒▒▒▒▒▒▒▒░██████████▓▓▓▓▓▓▓▓▓▓▓▓██▒░▒░░░▓█░░░░░░░    __________________________________________
░░░░░░░░░░▓█▒▒▒▒▒█▒▒░▒█░▒▒▒▓▒▒▒█▓▒▒▒▒▒▒░░░▓▓▒▒░░░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░██░░░░░░░  /                                          \\
░░░░░░░░░░░▓█▒▒▒▒█▒░░▒▓░░░░░░░░█▒▒▒▒▒▒░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒░░░░▒▒▓▓▓█▒░░░░░░░░  |  Still searching for answers, are we?     |
░░░░░░░░░░░░▒█▓▒▒█▒▒▒▓▓▒░░░░░░░▓▒▒▒▒▒▒░░░░▓▓▒▒▓▓▒▒▓▓░▒▒▒▒▓▓▓▓▓▓▓▓█▓▓▓▒░░░░░░░░░░░ -|  Perhaps I'll take a look... I suppose    |
░░░░░░░░░░░░░▓████████▓▓█░░░░░░▒▓▒▒▒▒░░░░░▓░░░▓▒░▒▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  |  it would be worth MY time.               |
░░░░░░░░░░░░█▓▓▓▓▓▓▓▓▓▓▓█▓░░░░░░▓░░░░░░▒░▓░░░░▓▒░█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  \\__________________________________________/
░░░░░░░░░░░▒█▓▓▓▓▓▓▓▓▓▓▓█▒░░░░░░░▓▒░░░░▓▓░░░░░▓▒▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░▒█▓▓▓▓▓▓▓▓▓▓██░░░░░░░░░▒▓▓▒▒░░░▓▓▓▓█▒▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░▒▓▓█████████▓░░░░░░░░░░░░░░░▓▓▓▓███▒▓▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░░ 
    
    """
    
    complete_ascii_art = """
    
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▒▒▒▒▒▒▒▒▒▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▒▒░░░░░░░░░░░░░░░░░░░▒▓▓▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒░░░░░░░░▒░░░░░░░░░░░░░░░░░░▒▒▓▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓░░░░▒░░░░░░░▒▒▓▓▓▓▓░░░░░░░░░░░░░░░░▓▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░░░░░░▒▓▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░░░░░▒▓░░░░░░░░░▒▓███▓░░░░░░░░░░░░░░░░░░░░▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒░░░░░░░▒████▓░▒██████████▓▒░░░░░░░░░░░░░░░░░▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░░░░░░▓███████████▓▓▒▒▓▓███████▓▒░░░░░░░░░░░░▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░▒▓███▓▒▒▒▓██▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░▒▓██▓▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░▒▓▓▓▒▒░░░░░░░░░░░░░▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░▒▒▒▒░░░▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░░░░░░░░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▓▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░▓▓▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░▒▒▒▒▒▒▒▒▒▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░▓▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░░░░▒▒▒▒▒▒▒▒▒▒▒▓▒░▒▒▒▒▒▒▒▒▒▓▒░░░░░░▓▓▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓░░░░▒░▒▒▒▒▒░░▒▒░▒▓██▓▒░▒▒▓█▓▒░▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▒▒░▒█▓▒░░░▓▒░▒▓▓░░░░░░▒▒░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░▓▓▓░▒▒░▒░░▓▓▒░░░░░▒▒░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░░▒▒▒░░░░▒▒░░░░░░░▒▒░░▒▒░░░░░░▒▓▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░▒▒░░░░░░▒▓▒▒▒▒▒▒░░░░▒▒▒▓█▓▒░░░▓▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒░░░░░░░▒▒░░░░░░░░▒▒░▒▓▓▓▓▓▒░░▓▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░▒▓░░░░░░░░▒░░░░░▒▒▒░░░░▓▓▓▓▓▓▓░░▓▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░▒▒▓▓▓▒░░░░░░░░▒▒▓▒▒░░░░░░▒▓▓▓▓▓▓▓▒░░▓▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░▓▓▓▓▓░░░░░░░░░▒░░░░░░░▓▓▓▓▓▓▓▓▒▓▓▒░▓▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░▒▓▓▓▓░░░░░░░░░▒▒░▒▓▓▓▓▓▓▓▓▓▓▒▒▒▓▒░▒▓▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░▒▓▓▓░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓▒▓▒▒▓▓░░▒▓▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░▒█░░░░░░░░░░▓▓▓▓▓▓▓▓▓▒▒▒▓▓░░░▒▓▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░▒▒░░░░░░░░░▒▓▓▓▓▓▓▓▓▓▒░░░░░▓▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░▓░░░░░░░░░▒▓▓▓▓▓▒░░░░░░▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░░░░░░░░▒░░░░░░░░░▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░▒▓▒▒▒▒▒▒▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▒▒▒▒▒▒▓░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒▒▓▒▒▒░▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒░▒▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒▒▒▒▒▒▒▒▒░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▒░▒▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▓▓▒▓▓▒░▒▓▒▒▒░░░░░▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓█▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▒▒▒▓▓▓▒▒▒▒▒▒▒▒░▒░░░░░░░░▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓█▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▒▒▓▓▒▓▓▒▒▒▒▒░░░░░░░░░░░░░░▒▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓█▓▓▓▓▓▓▓▓▓▓████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▒▒▓▓▒▒░░░░░░░░░░░░░░░░░▓▒░░░░▒█▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓██▓▓▓▓▓▓▓▓██████▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒
▓▓▓▒░░░░░░░░░░░░░░░▒▓▓▓█▒░▒▓████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓███▓▓▓▓▓▓████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█████▓▓▓▓███████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█████▓▓█████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ You're WELCOME!
    
    """
      
    agent = LLMAgent(
        name="Squilliam Fancyson",
        task=agent_task,
        prior_context="",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools=tools,
        verbose=False,
        max_plan_steps=10,
        ascii_art = challenged_ascii_art
    )
    

    
    result = agent.run(max_iterations=10)

    agent.print_ascii_art(ascii_art=complete_ascii_art)
    
    console = Console(file=sys.stderr)
    output_text = Text(result.final_output)
    output_panel = Panel(output_text, title="Final Output", border_style="bold cyan", expand=False)
    console.print(output_panel)
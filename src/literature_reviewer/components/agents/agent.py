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

"""


import datetime, json, logging, shutil, sys
from pydantic import BaseModel
from typing import List, Dict
from literature_reviewer.components.agents.model_call import ModelInterface
from literature_reviewer.components.tool import BaseTool, ToolResponse
from datetime import datetime, timezone
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax


"""
=======================================================
Data Models
=======================================================
"""
class AgentPlanStep(BaseModel):
    step: str
    reason: str
    prompt: str
    tool_name: str | None = None

    def as_rich(self) -> Panel:
        content = Text()
        content.append(f"Step: ", style="bold")
        content.append(self.step, style="cyan")
        content.append("\nReason: ", style="bold")
        content.append(self.reason, style="green")
        content.append("\nPrompt: ", style="bold")
        content.append(self.prompt, style="yellow")
        content.append("\nTool: ", style="bold")
        content.append(self.tool_name or "None", style="magenta")
        return Panel(content, title=f"Plan Step", border_style="blue")


class AgentPlan(BaseModel):
    steps: List[AgentPlanStep]
    
    def as_rich(self) -> Panel:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Step", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        table.add_column("Tool", style="yellow")
        
        for i, step in enumerate(self.steps, 1):
            table.add_row(str(i), step.step, step.tool_name or "None")
        
        return Panel(table, title="Agent Plan", border_style="blue")

    def as_formatted_text(self) -> str:
        formatted_text = "Agent Plan:\n"
        for i, step in enumerate(self.steps, 1):
            formatted_text += f"\nStep {i}:\n"
            formatted_text += f"  Action: {step.step}\n"
            formatted_text += f"  Reason: {step.reason}\n"
            formatted_text += f"  Tool: {step.tool_name or 'None'}\n"
        return formatted_text


class PlanStepResult(BaseModel):
    plan_step: AgentPlanStep
    result: ToolResponse

    def as_rich(self) -> Panel:
        content = Text()
        content.append("Plan Step:\n", style="bold")
        content.append(self.plan_step.step, style="cyan")
        content.append("\n\nTool: ", style="bold")
        content.append(self.plan_step.tool_name or "None", style="magenta")
        content.append("\n\nResult:\n", style="bold")
        content.append(f"Output: {self.result.output.strip()}", style="green")
        if self.result.explanation:
            content.append(f"\nExplanation: {self.result.explanation.strip()}", style="yellow")
        return Panel(content, title="Plan Step Result", border_style="cyan")


class PlanStepResultList(BaseModel):
    plan_steps: List[PlanStepResult]
    
    def as_rich(self) -> Panel:
        content = Group(*[step_result.as_rich() for step_result in self.plan_steps])
        return Panel(content, title="Plan Step Results", border_style="green")


class AgentReviewVerdict(BaseModel):
    verdict: bool
    recommendation: str | None
    revision_location: str | None
    
    def as_rich(self) -> Panel:
        content = Text()
        content.append("Verdict: ", style="bold")
        content.append("✅ Passed" if self.verdict else "❌ Failed", style="green" if self.verdict else "red")
        if self.recommendation:
            content.append("\n\nRecommendation:\n", style="bold")
            content.append(self.recommendation, style="italic yellow")
        if self.revision_location:
            content.append("\n\nRevision Location:\n", style="bold")
            content.append(self.revision_location, style="blue underline")
        return Panel(content, title="Review Verdict", border_style="magenta")


class AgentTask(BaseModel):
    action: str
    desired_result: str
    
    def as_rich(self) -> Panel:
        content = Text()
        content.append("Action:\n", style="bold")
        content.append(self.action, style="cyan")
        content.append("\n\nDesired Result:\n", style="bold")
        content.append(self.desired_result, style="green")
        return Panel(content, title="Agent Task", border_style="yellow")
    
    def as_xml_string(self) -> str:
        return (
            f"<agent_task>\n"
            f"  <action>{self.action}</action>\n"
            f"  <desired_result>{self.desired_result}</desired_result>\n"
            f"</agent_task>\n"
        )


class AgentProcessOutput(BaseModel):
    task: AgentTask
    iterations: int
    final_plan: str
    final_output: str
    final_review: str | None
    
    def as_rich(self) -> Panel:
        content = [
            self.task.as_rich(),
            Text(f"\nIterations: ", style="bold") + Text(str(self.iterations), style="cyan"),
            Text("\nFinal Plan:\n", style="bold") + Text(self.final_plan, style="green"),
            Text("\nFinal Output:\n", style="bold") + Text(self.final_output, style="yellow"),
        ]
        if self.final_review:
            content.append(Text("\nFinal Review:\n", style="bold") + Text(self.final_review, style="magenta"))
        return Panel(Group(*content), title="Agent Process Output", border_style="blue")


class AgentRevisionTask(BaseModel):
    task: str
    reason: str

    def as_rich(self) -> Panel:
        content = Text()
        content.append("Task:\n", style="bold")
        content.append(self.task, style="cyan")
        content.append("\n\nReason:\n", style="bold")
        content.append(self.reason, style="green")
        return Panel(content, title="Revision Task", border_style="yellow")


class AgentOutputRevision(BaseModel):
    revision_tasks: List[AgentRevisionTask]
    revised_output: str

    def as_rich(self) -> Panel:
        content = Text()
        for i, task in enumerate(self.revision_tasks, 1):
            content.append(f"\n{i}. ", style="bold")
            content.append(task.as_rich())
        content.append("\n\nRevised Output:\n", style="bold")
        content.append(self.revised_output, style="cyan")
        return Panel(content, title="Output Revision", border_style="green")


class ConversationHistoryEntry(BaseModel):
    agent_name: str
    heading: str
    timestamp: str
    model: str
    content: str
    content_structure: str

    def as_rich(self) -> Panel:
        details = Text()
        details.append(self.heading, style="bold yellow")
        details.append(f"\nTimestamp: ", style="dim")
        details.append(self.timestamp, style="cyan")
        details.append(f"\nModel: ", style="dim")
        details.append(self.model, style="magenta")
        
        details_panel = Panel(details, title="Entry Details", border_style="yellow", padding=(1, 1))
        
        if self.content_structure:
            try:
                model_class = globals()[self.content_structure]
                parsed_content = model_class.parse_raw(self.content)
                content_panel = parsed_content.as_rich()
            except (KeyError, ValueError) as e:
                content_panel = Panel(f"Error formatting content: {str(e)}", title="Content", border_style="red", padding=(1, 1))
        else:
            content_panel = Panel(Markdown(self.content), title="Content", border_style="green", padding=(1, 1))
        
        return Panel(Group(details_panel, content_panel), title=f"{self.agent_name} - {self.heading}", border_style="blue", padding=(1, 1))


class ConversationHistoryEntryList(BaseModel):
    entries: List[ConversationHistoryEntry]
    
    def as_rich(self) -> Panel:
        content = Group(*[entry.as_rich() for entry in self.entries])
        return Panel(content, title="Conversation History", border_style="cyan")


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


    def print_ascii_art(self):
        console = Console(file=sys.stderr)

        def create_ascii_art(text):
            width = len(text) + 2  # Reduced padding
            ascii_art = text
            return ascii_art.strip()

        # Create the inner ASCII art
        inner_ascii = create_ascii_art(self.name)
        
        # Create a Text object with the ASCII art, styled in magenta
        inner_text = Text(inner_ascii, style="bold magenta")

        # Create the inner panel with rounded borders
        inner_panel = Panel(
            inner_text,
            box=ROUNDED,
            border_style="bold magenta",
            expand=False,
            padding=(0, 0)  # Minimal padding
        )

        # Create the outer panel with rounded borders
        outer_panel = Panel(
            inner_panel,
            box=ROUNDED,
            border_style="bold cyan",
            expand=False,
            padding=(0, 0)  # Minimal padding
        )

        # Print the nested panels
        console.print(outer_panel)

    def print_latest_entry(self, entry):
        console = Console(file=sys.stderr)
        
        # Create the main panel content
        main_content = []
        
        # Add the details panel with spacing
        details = Text()
        details.append(entry.heading, style="bold yellow")
        details.append(f"\nTimestamp: ", style="dim")
        details.append(entry.timestamp, style="cyan")
        details.append(f"\nModel: ", style="dim")
        details.append(entry.model, style="magenta")
        
        details_panel = Panel(details, title="Entry Details", border_style="yellow", padding=(1, 1))
        main_content.append(details_panel)
        
        # Add the content panel with spacing, unless it's ASCII art
        if entry.content_structure:
            try:
                model_class = globals()[entry.content_structure]
                parsed_content = model_class.parse_raw(entry.content)
                content_panel = parsed_content.as_rich()
                
                # Apply padding to the content panel if it's not ASCII art
                if not isinstance(content_panel, (Panel, Text)) or "ASCII" not in str(content_panel):
                    if isinstance(content_panel, Panel):
                        content_panel.padding = (1, 1)
                    else:
                        content_panel = Panel(content_panel, padding=(1, 1), border_style="green")
                
                main_content.append(content_panel)
            except (KeyError, ValueError) as e:
                error_panel = Panel(f"Error formatting content: {str(e)}", title="Content", border_style="red", padding=(1, 1))
                main_content.append(error_panel)
        else:
            content_panel = Panel(Markdown(entry.content), title="Content", border_style="green", padding=(1, 1))
            main_content.append(content_panel)
        
        # Create the main panel with the content
        main_panel = Panel(
            Group(*main_content),
            title=f"{entry.agent_name} - {entry.heading}",
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
        self.print_ascii_art()  # Print ASCII art at the beginning of the run
        
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


class O1Agent:
    def __init__(self):
        pass
    
    
        
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    from literature_reviewer.components.agents.frameworks_and_models import ( #noqa
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
        action="Create a poem backed by concepts discussed by famous scientists, mention their scholarly work, but it's not necessary to cite or get exact works. First, gather ideas, second, find the key themes, third, write the poem",
        desired_result="A poem backed by concepts discussed by famous scientists",
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
    
    agent = LLMAgent(
        name="Academic Poem Writer",
        task=agent_task,
        prior_context="Chazal et al wrote about spine ligaments in 1984",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools=tools,
        verbose=True,
        max_plan_steps=10
    )
    
    result = agent.run(max_iterations=10)
        
    # Print the final output in a labeled box
    agent.print_ascii_art()
    
    console = Console(file=sys.stderr)
    output_text = Text(result.final_output)
    output_panel = Panel(output_text, title="Final Output", border_style="bold cyan", expand=False)
    console.print(output_panel)
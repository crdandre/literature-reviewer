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


import datetime, json, logging, sys
from pydantic import BaseModel
from typing import List, Dict
from literature_reviewer.components.agents.model_call import ModelInterface
from literature_reviewer.components.tool import BaseTool, ToolResponse
from datetime import datetime, timezone


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


class AgentPlan(BaseModel):
    steps: List[AgentPlanStep]
    
    def as_xml_string(self) -> str:
        steps_xml = "\n".join([
            f"  <step>\n"
            f"    <description>{step.step}</description>\n"
            f"    <reason>{step.reason}</reason>\n"
            f"    <prompt>{step.prompt}</prompt>\n"
            f"    <tool>\n"
            f"      <name>{step.tool.name if step.tool else 'None'}</name>\n"
            f"      <description>{step.tool.description if step.tool else 'None'}</description>\n"
            f"    </tool>\n"
            f"  </step>"
            for step in self.steps
        ])
        return f"<agent_plan>\n{steps_xml}\n</agent_plan>"
    
    def as_formatted_text(self) -> str:
        formatted_text = "Agent Plan:\n"
        for i, step in enumerate(self.steps, 1):
            formatted_text += f"\n{i}. {step.step}\n"
            formatted_text += f"   -> Reason: {step.reason}\n"
            formatted_text += f"   -> Prompt: {step.prompt}\n"
            formatted_text += f"   -> Tool Name: {step.tool_name if step.tool_name else 'None'}"
        return formatted_text


class PlanStepResult(BaseModel):
    plan_step: AgentPlanStep
    result: ToolResponse

    
class PlanStepResultList(BaseModel):
    plan_steps: List[PlanStepResult]
    
    def as_formatted_text(self) -> str:
        formatted_text = "Plan Step Results:\n"
        for i, step_result in enumerate(self.plan_steps, 1):
            formatted_text += f"\n{i}. Step: {step_result.plan_step.step}\n\n"
            formatted_text += f"   Tool: {step_result.plan_step.tool_name if step_result.plan_step.tool_name else 'None'}\n\n"
            formatted_text += f"   Result:\n"
            formatted_text += f"   Output: {step_result.result.output.strip()}\n\n"
            if step_result.result.explanation:
                formatted_text += f"   Explanation: {step_result.result.explanation.strip()}"
        return formatted_text


class AgentReviewVerdict(BaseModel):
    verdict: bool
    recommendation: str | None
    revision_location: str | None
    
    def as_formatted_text(self) -> str:
        formatted_text = f"Review Verdict:\n\n"
        formatted_text += f"Verdict: {'Passed' if self.verdict else 'Failed'}\n\n"
        if self.recommendation:
            formatted_text += f"Recommendation: {self.recommendation}\n\n"
        if self.revision_location:
            formatted_text += f"Revision Location: {self.revision_location}"
        return formatted_text
        


class AgentTask(BaseModel):
    action: str
    desired_result: str
    
    def as_xml_string(self) -> str:
        return (
            f"<agent_task>\n"
            f"  <action>{self.action}</action>\n"
            f"  <desired_result>{self.desired_result}</desired_result>\n"
            f"</agent_task>\n"
        )

    def as_formatted_text(self) -> str:
        return f"Action: {self.action}\n\nDesired Result: {self.desired_result}"


class AgentProcessOutput(BaseModel):
    task: AgentTask
    iterations: int
    final_plan: str
    final_output: str
    final_review: str | None
    
    def as_formatted_text(self) -> str:
        return (
            f"Task:\n{self.task.as_formatted_text()}\n\n"
            f"Final Review:\n{self.final_review}\n\n"
            f"Iterations: {self.iterations}\n\n"
            f"Final Plan:\n{self.final_plan}\n\n"
            f"Final Output:\n{self.final_output}"
        )

class AgentRevisionTask(BaseModel):
    task: str
    reason: str

class AgentOutputRevision(BaseModel):
    revision_tasks: List[AgentRevisionTask]
    revised_output: str

    def as_formatted_text(self) -> str:
        formatted_text = "Output Revision:\n"
        for i, task in enumerate(self.revision_tasks, 1):
            formatted_text += f"\n{i}. Task: {task.task}\n"
            formatted_text += f"   Reason: {task.reason}\n"
        formatted_text += f"\nRevised Output:\n\n{self.revised_output}"
        return formatted_text

class ConversationHistoryEntry(BaseModel):
    agent_name: str
    heading: str
    timestamp: str
    model: str
    content: str
    content_structure: str  # Name of the Pydantic model

    def as_formatted_text(self) -> str:
        if self.content_structure:
            try:
                # Get the class from the current module
                model_class = globals()[self.content_structure]
                # Parse the content string back into the Pydantic model
                parsed_content = model_class.parse_raw(self.content)
                # Call the as_formatted_text method of the parsed content
                formatted_content = parsed_content.as_formatted_text()
            except (KeyError, ValueError) as e:
                formatted_content = f"Error formatting content: {str(e)}"
        else:
            formatted_content = self.content

        return f"[{self.timestamp}] {self.agent_name} - {self.heading}\n\nModel: {self.model}\n\nContent:\n{formatted_content}"


class ConversationHistoryEntryList(BaseModel):
    entries: List[ConversationHistoryEntry]
    
    def as_xml_string(self) -> str:
        entries_xml = "\n".join([
            f"  <entry>\n"
            f"    <heading>{entry.heading}</heading>\n"
            f"    <timestamp>{entry.timestamp}</timestamp>\n"
            f"    <model>{entry.model}</model>\n"
            f"    <content>{entry.content}</content>\n"
            f"  </entry>"
            for entry in self.entries
        ])
        return f"<conversation_history>\n{entries_xml}\n</conversation_history>"
    
    def as_formatted_text(self) -> str:
        formatted_entries = []
        for entry in self.entries:
            formatted_entry = (
                f"[{entry.timestamp}] {entry.agent_name} - {entry.heading}\n"
                f"Model: {entry.model}\n"
                f"Content: {entry.content}\n"
                f"{'-' * 40}"
            )
            formatted_entries.append(formatted_entry)
        
        return "\n".join(formatted_entries).strip()


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


    def print_latest_entry(self, entry):
        print(f"\n{'=' * 50}", file=sys.stderr)
        print(entry.as_formatted_text(), file=sys.stderr)
        print(f"{'=' * 50}", file=sys.stderr)  # Removed the leading newline
        sys.stderr.flush()


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
            
            if step.tool_name is None:
                # Handle steps without a tool
                result_json = self.model_interface.chat_completion_call(
                    system_prompt="You are a helpful assistant executing a task. Provide the result and a brief explanation.",
                    user_prompt=f"{step_prompt}\n\nRespond in ToolResponse format with 'output' and 'explanation' fields.",
                    response_format=ToolResponse
                )
                output = ToolResponse(**json.loads(result_json))
            else:
                if step.tool_name not in self.tools:
                    self.logger.warning(f"Tool '{step.tool_name}' not found for step: {step}")
                    continue
                
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
        
        # Extract the final result from the output
        final_output = self.extract_final_output(final_result)
        
        return AgentProcessOutput(
            task=self.task,
            iterations=iteration,
            final_plan=plan.as_formatted_text(),
            final_output=final_output,
            final_review=final_review
        )

    def extract_final_output(self, output):
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
        model=Model("gpt-4o","OpenAI"),
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
    
    agent.run(max_iterations=10)
    

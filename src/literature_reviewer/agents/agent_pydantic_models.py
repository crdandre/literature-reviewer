from pydantic import BaseModel
from typing import List
from literature_reviewer.components.tool import ToolResponse
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown


class AgentPlanStep(BaseModel):
    step: str
    reason: str
    prompt: str
    tool_name: str | None = None

    def as_rich(self) -> Panel:
        content = Text()
        content.append(f"Step: ", style="italic")
        content.append(self.step, style="cyan")
        content.append("\nReason: ", style="italic")
        content.append(self.reason, style="green")
        content.append("\nPrompt: ", style="italic")
        content.append(self.prompt, style="yellow")
        content.append("\nTool: ", style="italic")
        content.append(self.tool_name or "None", style="magenta")
        return Panel(content, title=f"Plan Step", border_style="blue")


class AgentPlan(BaseModel):
    steps: List[AgentPlanStep]
    
    def as_rich(self) -> Group:
        table = Table(title="Agent Plan", show_header=True, header_style="bold magenta")
        table.add_column("Step", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        table.add_column("Tool", style="yellow")
        
        for i, step in enumerate(self.steps, 1):
            table.add_row(str(i), step.step, step.tool_name or "None")
        
        return Group(table)

    def as_formatted_text(self) -> str:
        formatted_text=""
        for i, step in enumerate(self.steps, 1):
            formatted_text += f"Step {i}:\n"
            formatted_text += f"  Action: {step.step}\n"
            formatted_text += f"  Reason: {step.reason}\n"
            formatted_text += f"  Tool: {step.tool_name or 'None'}\n"
        return formatted_text


class PlanStepResult(BaseModel):
    plan_step: AgentPlanStep
    result: ToolResponse

    def as_rich(self) -> Group:
        content = Group(
            Text("\nPlan Step:", style="italic"),
            Text(self.plan_step.step, style="cyan"),
            Text("\nTool: ", style="italic"),
            Text(self.plan_step.tool_name or "None", style="magenta"),
            Text("\nResult:", style="italic"),
            Text(f"{self.result.output.strip()}", style="green")
        )
        if self.result.explanation:
            content.renderables.append(Text(f"\nExplanation:", style="italic"))
            content.renderables.append(Text(f"{self.result.explanation.strip()}", style="yellow"))
        return content


class PlanStepResultList(BaseModel):
    plan_steps: List[PlanStepResult]
    
    def as_rich(self) -> Group:
        return Group(*[step_result.as_rich() for step_result in self.plan_steps])


class AgentReviewVerdict(BaseModel):
    verdict: bool
    recommendation: str | None
    revision_location: str | None
    
    def as_rich(self) -> Group:
        content = Group(
            Text("Verdict: ", style="bold") + Text("✅ Passed" if self.verdict else "❌ Failed", style="green" if self.verdict else "red"),
        )
        if self.recommendation:
            content.renderables.append(Text("\nRecommendation:", style="bold"))
            content.renderables.append(Text(self.recommendation, style="italic yellow"))
        if self.revision_location:
            content.renderables.append(Text("\nRevision Location:", style="bold"))
            content.renderables.append(Text(self.revision_location, style="blue underline"))
        return content


class AgentTask(BaseModel):
    action: str
    desired_result: str
    
    def as_rich(self) -> Group:
        return Group(
            Text("Action:", style="italic"),
            Text(self.action, style="cyan"),
            Text("\nDesired Result:", style="italic"),
            Text(self.desired_result, style="green")
        )
    
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
    
    def as_rich(self) -> Group:
        content = [
            self.task.as_rich(),
            Text(f"\nIterations:", style="italic"),
            Text(str(self.iterations), style="bold cyan"),
            Text("\nFinal Plan:", style="italic"),
            Text(self.final_plan, style="bold green"),
            Text("\nFinal Output:", style="italic"),
            Text(self.final_output, style="bold yellow"),
        ]
        if self.final_review:
            content.append(Text("\nFinal Review:\n", style="italic") + Text(self.final_review, style="magenta"))
        return Group(*content)


class AgentRevisionTask(BaseModel):
    task: str
    reason: str

    def as_rich(self) -> Panel:
        content = Text()
        content.append("Task:\n", style="italic")
        content.append(self.task, style="cyan")
        content.append("\n\nReason:\n", style="italic")
        content.append(self.reason, style="green")
        return Panel(content, title="Revision Task", border_style="yellow")


class AgentOutputRevision(BaseModel):
    revision_tasks: List[AgentRevisionTask]
    revised_output: str

    def as_rich(self) -> Group:
        content = Group()
        content.renderables.append(Text("Output Revision", style="bold green"))
        
        for i, task in enumerate(self.revision_tasks, 1):
            task_panel = task.as_rich()
            content.renderables.append(Text(f"\n{i}. ", style="italic"))
            content.renderables.append(task_panel)
        
        content.renderables.append(Text("\nRevised Output:", style="italic bold"))
        content.renderables.append(Text(self.revised_output, style="cyan"))
        
        return content


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
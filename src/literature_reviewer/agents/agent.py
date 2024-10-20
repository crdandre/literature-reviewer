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
from typing import Dict, Any, Optional
from pydantic import ValidationError, create_model

from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.agent_pydantic_models import (
    AgentPlan,
    PlanStepResult,
    PlanStepResultList,
    AgentReviewVerdict,
    AgentProcessOutput,
    AgentOutputRevision,
    ConversationHistoryEntry,
    ConversationHistoryEntryList,
    ToolResponse
)
from literature_reviewer.agents.components.memory import (
    LoadingAnimation, run_with_loading, add_to_conversation_history
)
from literature_reviewer.agents.components.printout import print_ascii_art
from literature_reviewer.tools.basetool import BaseTool


class Agent:
    """
    An intelligent agent capable of planning and executing tasks.

    Attributes:
        name (str): The name of the agent.
        task (str): The task assigned to the agent.
        state (str): Any prior context or information given to the agent.
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
        task (str): The task assigned to the agent.
        state (str): Any prior context or information given to the agent.
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
        task: str,
        state: str,
        model_interface: ModelInterface,
        system_prompts,
        tools: Dict[str, BaseTool] | None,
        verbose,
        max_plan_steps=10,
        ascii_art=None,
        output_schema: Optional[Dict[str, Any]] = None
    ):
        self.model_interface = model_interface
        self.name = name
        self.task = task
        self.state = state
        self.system_prompts = system_prompts
        self.tools = tools
        self.verbose = verbose
        self.conversation_history = ConversationHistoryEntryList(entries=[])
        self.max_plan_steps = max_plan_steps
        self.ascii_art = ascii_art
        self.output_schema = output_schema
        
        if self.output_schema:
            self.DynamicOutput = create_model('DynamicOutput', **self.output_schema)
            self.AgentProcessOutputClass = AgentProcessOutput.with_dynamic_output(self.output_schema)
        else:
            self.DynamicOutput = None
            self.AgentProcessOutputClass = AgentProcessOutput
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.name}")
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        self.loading_animation = LoadingAnimation()
        
        if self.state:
            self.conversation_history.entries.append(ConversationHistoryEntry(
                agent_name=self.name,
                heading="Prior Context",
                timestamp=datetime.now(timezone.utc).isoformat(),
                model=self.model_interface.model.model_name,
                content=self.state,
                content_structure="str"
            ))
            self.logger.debug(f"Added prior context: {self.state}")


    @run_with_loading
    @add_to_conversation_history
    def create_plan(self):
        """
        Gets agent-specific prompt for creating a step-by-step plan
        to accomplish the task within agent scope
        """
        self.logger.debug("Starting planning process")
        
        tool_specs = {name: tool.__doc__ for name, tool in self.tools.items()} if self.tools else None
        
        # Determine if this is a triage agent
        is_triage = self.name.lower() == "triage"

        # Prepare the system prompt based on agent type
        if is_triage:
            system_prompt = self.system_prompts.get("triage_planning")(
                max_steps=self.max_plan_steps,
                available_agents=self.available_agents,
                output_schema=json.dumps(self.output_schema, indent=2)
            )
        else:
            system_prompt = self.system_prompts.get("planning")(
                max_steps=self.max_plan_steps,
                tool_specs=tool_specs
            )
        
        # Prepare the user prompt
        user_prompt = f"Task: Given, {self.state}, do {self.task} please!"

        # Make the model call
        plan_json = self.model_interface.chat_completion_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
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
        step_outputs = {}

        for step in plan.steps:
            step_prompt = f"{accumulated_context}\n\nCurrent step: {step.prompt}"
            
            if self.tools is None or step.tool_name is None or step.tool_name not in self.tools:
                try:
                    result_json = self.model_interface.chat_completion_call(
                        system_prompt="You are a helpful assistant executing a task. Provide the result and a brief explanation.",
                        user_prompt=f"{step_prompt}",
                        response_format=ToolResponse
                    )
                    if result_json is None or not isinstance(result_json, str):
                        raise ValueError("Invalid response from model_interface")
                    output = ToolResponse(**json.loads(result_json))
                except Exception as e:
                    self.logger.error(f"Error in chat completion call: {str(e)}")
            else:
                try:
                    tool = self.tools[step.tool_name]
                    tool.set_output_schema(self.output_schema)
                    
                    # TODO: make this generic
                    # Check if the tool requires input from a previous step
                    if step.tool_name == 'gather_corpus' and 'generate_queries' in step_outputs:
                        # Update the tool's search_queries attribute with the output from the previous step
                        tool.search_queries = json.loads(step_outputs['generate_queries'])['queries']
                    
                    # Pass the updated prompt with accumulated context to the tool
                    step.prompt = step_prompt
                    output = tool.use(step)
                    
                    # Store the output for potential use in future steps
                    step_outputs[step.tool_name] = output.output
                except Exception as e:
                    self.logger.error(f"Error executing step '{step}' with tool '{step.tool_name}': {str(e)}")
                    continue
            
            # Pass the ToolResponse object directly
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
        Task: {self.task}
        
        Output to review:
        {output}
        
        Please review the output and determine if it successfully completes the task.
        Provide detailed feedback, including strengths and areas for improvement.
        """
        
        # Check if this is the Triage agent
        if self.name.lower() == "triage":
            system_prompt = self.system_prompts.get("review")(
                available_agents=self.available_agents,
                output_schema=self.output_schema
            )
        else:
            system_prompt = self.system_prompts.get("review")()
        
        review_result = self.model_interface.chat_completion_call(
            system_prompt=system_prompt,
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
        Original Task: {self.task}
        
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
        Original Task: {self.task}
        
        Original Output:
        {output}
        
        Review Feedback:
        {feedback}
        
        Please revise the output based on the feedback provided. Ensure the revised output addresses the issues raised in the feedback and better fulfills the original task.
        """
        
        revised_output_json = self.model_interface.chat_completion_call(
            system_prompt=self.system_prompts.get("revise_output")(output),
            user_prompt=revision_prompt,
            response_format=self.DynamicOutput if self.DynamicOutput else AgentOutputRevision,
        )
        
        return self.DynamicOutput(**json.loads(revised_output_json)) if self.DynamicOutput else AgentOutputRevision(**json.loads(revised_output_json))


    @add_to_conversation_history
    def run(self, max_iterations, state="", output_schema: Optional[Dict[str, Any]] = None):
        print_ascii_art(self.ascii_art)
        
        print("STATE TO ADD: ", state)
        if isinstance(state, str):
            try:
                state_dict = json.loads(state)
                self.state += json.dumps(state_dict, indent=2)
            except json.JSONDecodeError:
                self.state += state
        else:
            self.state += json.dumps(state, indent=2)

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
            
            if self.DynamicOutput:
                final_output = self.DynamicOutput(**json.loads(final_output))
            
            return self.AgentProcessOutputClass(
                task=self.task,
                iterations=iteration,
                final_plan=plan.as_list(),
                final_output=final_output,
                final_review=final_review
            ).model_dump()

        finally:
            self.loading_animation.stop()
            sys.stdout.flush()


    def _extract_final_output(self, output):
        if isinstance(output, PlanStepResultList) and output.plan_steps:
            last_step = output.plan_steps[-1]
            return last_step.result.output
        elif isinstance(output, str):
            return output
        return json.dumps({"error": "No output generated"})
    
    #for triage agent
    def set_available_agents(self, available_agents):
        self.available_agents = available_agents
    
    def set_triage_attributes(self, available_agents, output_schema):
        self.available_agents = available_agents
        self.output_schema = self._make_json_serializable(output_schema)

    def _make_json_serializable(self, obj):
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(v) for v in obj]
        elif isinstance(obj, type):
            return str(obj)
        else:
            return obj
        
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
    from literature_reviewer.tools.corpus_gatherer import CorpusGatherer
    from literature_reviewer.tools.cluster_analyzer import ClusterAnalyzer
    
    # agent_task = "cluster the embedded corpus, and analyze the clusters, outputting a summary of them using analyze_clusters",
    agent_task = "write a plan for how to collect literature sources to do a literature review"


    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini","OpenAI"),
    )

    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt_ais.txt", "r") as file:
        user_goals_text = file.read()
    user_supplied_pdfs_directory = "/home/christian/literature-reviewer/user_inputs/user_supplied_pdfs"
    num_vec_db_queries = 3
    vec_db_query_num_results = 2
    num_s2_queries = 2
    
    pdf_download_path = "/home/christian/literature-reviewer/test_outputs/downloaded_pdfs"
    vector_db_path = "/home/christian/literature-reviewer/test_outputs/chroma_db"

    
    """
    model_interface should be inherited from the agent by default?
    serial outputs (i.e. tool input dependent on prior tool output as in search_queries)
    should be handled more explicitly. better tool spec should be given. i.e. define i/o formats?
    get inspiration from existing agent 
    maybe strict tool use order requirements for steps too.
    
    missing: generic behavior requirements i.e. force use X tool, use prior output of Y format
    in this pattern (i.e. iterate through search queries and address each individually, etc.)
    
    fwiw, some pdfs aren't downloaded. it's worth noting the relevant titles and abstracts because
    most don't have open access pdfs
    
    logging within tools would be nice too to see what's going on with things like paper inclusion
    """
    tools = {
        "generate_queries": ResearchQueryGenerator(
            user_goals_text=user_goals_text,
            user_supplied_pdfs_directory=user_supplied_pdfs_directory,
            model_interface=model_interface,
            num_vec_db_queries=num_vec_db_queries,
            vec_db_query_num_results=vec_db_query_num_results,
            num_s2_queries=num_s2_queries,
        ),
        "gather_corpus": CorpusGatherer(
            search_queries=None,  # This will be updated dynamically
            user_goals_text=user_goals_text,
            model_interface=model_interface,
            pdf_download_path=pdf_download_path,
            chromadb_path=vector_db_path,
        ),
        "analyze_clusters": ClusterAnalyzer(
            model_interface=model_interface,
            user_goals_text=user_goals_text,
            max_clusters_to_analyze=999,
            num_keywords_per_cluster=12,
            num_chunks_per_cluster=12,
            reduced_dimensions=120,
            dimensionality_reduction_method="PCA",
            clustering_method="HDBSCAN",
            chromadb_path=vector_db_path,
        )
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
        state="",
        model_interface=model_interface,
        system_prompts=system_prompts,
        tools=tools,
        verbose=True,
        max_plan_steps=1,
        ascii_art = challenged_ascii_art
    )
    
    agent.run(max_iterations=3)
    print_ascii_art(ascii_art=complete_ascii_art)






"""
Module to create reflections between any grouping of steps
with respect to one output step or objective

I.e. "Examine the chain of reasoning in Processes N-M that
led to X paper being selected as connected to Y objective"

The module should be as flexible as possible.

Ideas:
1. Accumulate chat context and prompt the model to reflect on it
2. "Continuous Attention"?
3. "Meta-learning"?
4. some hybrid approach?
5. Event driven/triggered or continuously monitoring execution and able to interject?

Initial o1 example
"""
from typing import List, Optional, Dict
import json
from literature_reviewer.components.input_output_models.process_interfacing import ProcessStep
from literature_reviewer.components.model_interaction.model_call import ModelInterface

class ReflectionOperator:
    def __init__(
        self,
        input_steps: List[ProcessStep],
        output_objective: str,
        user_context: str,
        model_interface: ModelInterface,
        max_iterations: int = 3
    ):
        self.input_steps = input_steps
        self.output_objective = output_objective
        self.user_context = user_context
        self.model_interface = model_interface
        self.max_iterations = max_iterations
        self.current_iteration = 0

    def perform_reflection(self):
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1
            print(f"Reflection Iteration: {self.current_iteration}")

            # Collect outputs from input steps
            input_data = self.collect_input_data()
            
            # Construct reflection prompt
            prompt = self.construct_prompt(input_data)
            
            # Call the LLM to perform reflection
            reflection_output = self.model_interface.entry_chat_call(
                system_prompt="Your reflection system prompt here.",
                user_prompt=prompt,
                response_format="json"  # Assuming JSON format for structured output
            )
            
            # Process the reflection output
            adjustments_needed = self.process_reflection(reflection_output)
            
            # Apply adjustments if necessary
            if adjustments_needed:
                self.apply_adjustments(adjustments_needed)
                print(f"Adjustments applied based on reflection: {adjustments_needed}")
            else:
                print("No adjustments needed. Reflection process is coherent.")
                break  # Exit early if no adjustments are needed

    def collect_input_data(self) -> str:
        collected_data = ""
        for step in self.input_steps:
            collected_data += f"\nStep {step.name}:\n"
            collected_data += f"Task: {step.task}\n"
            collected_data += "Subtasks:\n"
            for subtask in step.subtasks:
                collected_data += f"- {subtask}\n"
        return collected_data

    def construct_prompt(self, input_data: str) -> str:
        # Create a prompt for the LLM that includes the input data, user context, and output objective
        prompt = f"""
User Context:
{self.user_context}

Output Objective:
{self.output_objective}

Input Data from Selected Steps:
{input_data}

Please reflect on whether the input data aligns with the user's goals and the output objective. Provide suggestions for improvements or confirm that the outputs are coherent and satisfactory. If adjustments are needed, specify them in a JSON format as follows:

{{
    "adjustments": {{
        "step_name": "Name of the step to adjust",
        "modification": "Description of the required modification"
    }}
}}
"""
        return prompt

    def process_reflection(self, reflection_output: str) -> Optional[Dict[str, str]]:
        """
        Analyze the reflection output from the LLM.
        Expecting a JSON response with adjustments if needed.
        Example:
        {
            "adjustments": {{
                "step_name": "Cluster Analysis",
                "modification": "Increase the number of clusters to better capture thematic diversity."
            }}
        }
        """
        try:
            reflection_data = json.loads(reflection_output)
            adjustments = reflection_data.get("adjustments", None)
            return adjustments
        except json.JSONDecodeError:
            print("Failed to decode reflection output. Assuming no adjustments.")
            return None

    def apply_adjustments(self, adjustments: Dict[str, str]):
        """
        Apply the suggested adjustments to the input steps or their outputs.
        """
        for step in self.input_steps:
            if step.name == adjustments.get("step_name"):
                # Example adjustment: Modify the task or subtasks based on the reflection
                modification = adjustments.get("modification")
                print(f"Applying modification to step '{step.name}': {modification}")
                # Here, implement the logic to modify the step based on the instruction
                # This is a placeholder and should be replaced with actual modification logic
                step.task = modification  # Simplistic example
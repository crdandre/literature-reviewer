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
from typing import List
from literature_reviewer.components.input_output_models.process_interfacing import ProcessStep
from literature_reviewer.components.model_interaction.model_call import ModelInterface

class ReflectionOperator:
    def __init__(
        self,
        input_steps: List[ProcessStep],
        output_objective: str,
        user_context: str,
        model_interface: ModelInterface,
        max_iterations: int = 1
    ):
        self.input_steps = input_steps
        self.output_objective = output_objective
        self.user_context = user_context
        self.model_interface = model_interface
        self.max_iterations = max_iterations

    def perform_reflection(self):
        for iteration in range(self.max_iterations):
            # Collect outputs from input steps
            input_data = self.collect_input_data()
            
            # Construct reflection prompt
            prompt = self.construct_prompt(input_data)
            
            # Call the LLM to perform reflection
            reflection_output = self.model_interface.entry_chat_call(
                system_prompt="Your reflection system prompt here.",
                user_prompt=prompt,
                response_format=None  # Define appropriate response format if needed
            )
            
            # Process the reflection output
            adjustments_needed = self.process_reflection(reflection_output)
            
            # Apply adjustments if necessary
            if adjustments_needed:
                self.apply_adjustments(adjustments_needed)
            else:
                # If no adjustments are needed, you can break early
                break

    def collect_input_data(self) -> str:
        # Collect outputs from the specified input steps
        collected_data = ""
        for step in self.input_steps:
            # Assuming each ProcessStep has an 'output_data' attribute
            collected_data += f"\nStep {step.name} Output:\n{step.output_data}\n"
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

Please reflect on whether the input data aligns with the user's goals and the output objective. Provide suggestions for improvements or confirm that the outputs are coherent and satisfactory.
"""
        return prompt

    def process_reflection(self, reflection_output: str):
        # Analyze the reflection output from the LLM
        # Decide whether adjustments are needed and return them
        # This could involve parsing the output and extracting actionable suggestions
        adjustments = None  # Replace with actual processing logic
        return adjustments

    def apply_adjustments(self, adjustments):
        # Apply the suggested adjustments to the input steps or their outputs
        # This method would modify the steps or data in place or create updated versions
        pass
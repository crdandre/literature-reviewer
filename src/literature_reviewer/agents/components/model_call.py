"""
Handles prompting LLMs. Modular design should make using different
frameworks and providers somewhat doable as long as more don't keep
popping up quicker than I can keep track of
"""
from importlib import import_module
from literature_reviewer.agents.components.frameworks_and_models import ( #noqa
    PromptFramework, Model
)
from typing import Union, List

class ModelInterface:
    def __init__(
        self,
        prompt_framework: PromptFramework,
        model: Model
    ):
        self.prompt_framework = prompt_framework
        self.model = model
        self.framework_module = self._import_framework_module()
    
    
    def _import_framework_module(self):
        module_name = self.prompt_framework.value.lower()
        return import_module(
            f"literature_reviewer.agents.components.frameworks.{module_name}"
        )
    
    @staticmethod
    def _clean_prompts(system_prompt: str, user_prompt: str):
        """
        Remove leading and trailing newlines from system and user prompts.
        """
        cleaned_system_prompt = system_prompt.strip()
        cleaned_user_prompt = user_prompt.strip()
        
        return cleaned_system_prompt, cleaned_user_prompt

    def chat_completion_call(
        self,
        system_prompt,
        user_prompt,
        response_format=None,
        assistant_prompt=None,
        image_string=None,
        tools=None,
        tool_choice="required"
    ) -> str:
        """
        Calls an LLM API using the specified prompt framework and provider.
        """
        cleaned_system_prompt, cleaned_user_prompt = self._clean_prompts(
            system_prompt, user_prompt
        )
        if self.prompt_framework == PromptFramework.OAI_API:
            return self.framework_module.chat_completion_call(
                model_choice=self.model,
                system=cleaned_system_prompt,
                user=cleaned_user_prompt,
                response_format=response_format,
                assistant=assistant_prompt,
                base64_image_string=image_string,
                tools=tools,
                tool_choice=tool_choice,
            ) 
        else:
            raise NotImplementedError(f"Framework {self.prompt_framework} not implemented yet")


    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Calls an embedding model API using the specified prompt framework and provider.
        
        Args:
            texts: A single string or a list of strings to embed.
        
        Returns:
            If input is a single string, returns a list of floats (embedding).
            If input is a list of strings, returns a list of list of floats (embeddings).
        """
        if self.prompt_framework == PromptFramework.OAI_API:
            return self.framework_module.embed(
                model=self.model.model_name,
                input=texts
            )
        else:
            raise NotImplementedError(f"Framework {self.prompt_framework} not implemented yet")

"""
Handles prompting LLMs. Modular design should make using different
frameworks and providers somewhat doable as long as more don't keep
popping up quicker than I can keep track of
"""
from importlib import import_module
from literature_reviewer.components.model_interaction.frameworks_and_models import ( #noqa
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
            f"literature_reviewer.components.model_interaction.frameworks.{module_name}"
        )
    
    
    def entry_chat_call(
        self,
        system_prompt,
        user_prompt,
        response_format
    ) -> str:
        """
        Calls an LLM API using the specified prompt framework and provider.
        
        entry_call is currently a system,user call. In the future,
        it may be useful to have this be the entry-point where
        a decision about the optimal prompt type can be made.
        that could either be done here or in the framework files
        such as ell.py
        """
        if self.prompt_framework == PromptFramework.ELL:
            return self.framework_module.entry_chat_call(
                model=self.model.model_name,
                system=system_prompt,
                user=user_prompt,
                response_format=response_format
            )
        if self.prompt_framework == PromptFramework.OAI_API:
            return self.framework_module.entry_chat_call(
                model_choice=self.model,
                system=system_prompt,
                user=user_prompt,
                response_format=response_format
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

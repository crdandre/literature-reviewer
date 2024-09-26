"""
Handles prompting LLMs. Modular design should make using different
frameworks and providers somewhat doable as long as more don't keep
popping up quicker than I can keep track of
"""
from importlib import import_module
from literature_reviewer.components.model_interaction.frameworks_and_models import ( #noqa
    PromptFramework, Model, get_models_for_provider
)

class LLMInterface:
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
        return import_module(f"literature_reviewer.components.model_interaction.{module_name}")
    
    def entry_call(
        self,
        system_prompt,
        task_prompt
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
            return self.framework_module.entry_call(
                model=self.model.model_name,
                system=system_prompt,
                task=task_prompt
            )
        else:
            raise NotImplementedError(f"Framework {self.prompt_framework} not implemented yet")

    @staticmethod
    def get_available_models(provider: str) -> list[Model]:
        """
        Returns a list of available models for the given provider.
        """
        return get_models_for_provider(provider)


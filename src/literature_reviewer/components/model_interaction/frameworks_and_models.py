"""
Houses options for frameworks, providers, models
"""

from enum import Enum


class PromptFramework(Enum):
    LANGCHAIN = "LangChain"
    ELL = "ell"
    OAI_API = "openai"


class Model:
    def __init__(self, model_name: str, provider: str):
        self.model_name = model_name
        self.provider = provider


# MODELS = {
#     #chat
#     "gpt-4o-mini": Model("gpt-4o-mini", "OpenAI"),
#     # "gemini"
#     #embedding
#     "text-embedding-3-small": Model("text-embedding-3-small", "OpenAI"),
#     "text-embedding-3-large": Model("text-embedding-3-large", "OpenAI"),
# }


# def get_models_for_provider(provider: str) -> list[Model]:
#     return [model for model in MODELS.values() if model.provider == provider]

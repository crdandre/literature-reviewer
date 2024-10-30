"""
Houses options for frameworks, providers, models
"""

from enum import Enum


class PromptFramework(Enum):
    LANGCHAIN = "LangChain"
    OAI_API = "openai"


class Model:
    def __init__(self, model_name: str, provider: str):
        self.model_name = model_name
        self.provider = provider

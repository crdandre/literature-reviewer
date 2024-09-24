"""
Analyzes a given corpus.

1. RAG with batch of results based on given data
2. Given data is obtained from PDF upload, DOI search
    (which may include PDF reading from openAccessPdf url),
    or query/other search (may also include this PDF if OA)
    
This file only carries out the RAG functions. The corpus used
for RAG is determined upstream and passed into this class.
"""
from enum import Enum

# base logic in call on provider
class PromptFramework(Enum):
    LANGCHAIN = "LangChain"
    ELL = "ell"
    DIRECT_API = "direct_api"


# base url, credentials on provider
class ModelProvider(Enum):
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    DEEPSEEK = "DeepSeek"
    OLLAMA = "Ollama"


class LLMInterface:
    def __init__(
        self,
        prompt_framework: PromptFramework,
        model_provider: ModelProvider
    ):
        self.prompt_framework = prompt_framework
        self.model_provider = model_provider
    
    
    def call(
        self,
        system_prompt,
        task_prompt
    ) -> str:
        """
        uses a modular system to call an LLM from any OAI-compatible
        provider, and via either API call directly, LangChain, or ell
        """
        
        
        
        
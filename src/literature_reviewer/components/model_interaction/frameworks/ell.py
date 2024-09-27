"""
Library of prompting tools necessary for the agent using the 
ell framework.

This should inject prompts defined in prompts/ rather than
contain its own

entry_chat_call is a simple system,user call. In the future,
it may be useful to have this be the entry-point where
a decision about the optimal prompt type can be made
"""
import ell
from openai import OpenAI

#these should be around somewhere
ell.init(store="./logdir", autocommit=True)

# OLLAMA_HOST = "http://localhost:11434/v1"
# MODEL = "llama3.1:latest"
# ell.models.ollama.register(OLLAMA_HOST)

def entry_chat_call(model, system, task):
    @ell.simple(model=model)
    def _call(system, task):
        return [
            ell.system(system),
            ell.user(task)
        ]
    
    return _call(system,task)


def embed(model, input):
    client = OpenAI()
    
    if isinstance(input, str):
        input = [input.replace("\n", " ")]
    elif isinstance(input, list):
        input = [text.replace("\n", " ") for text in input]
    else:
        raise ValueError("Input must be a string or a list of strings")
    
    response = client.embeddings.create(input=input, model=model)
    
    if len(input) == 1:
        return response.data[0].embedding
    else:
        return [item.embedding for item in response.data]

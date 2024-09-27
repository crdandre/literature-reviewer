"""
Library of prompting tools necessary for the agent using the 
LangChain framework.

This should inject prompts defined in prompts/ rather than
contain its own
"""
from langchain_openai import OpenAIEmbeddings

def get_embedding_function(model):
    return OpenAIEmbeddings(
        model=model
    )


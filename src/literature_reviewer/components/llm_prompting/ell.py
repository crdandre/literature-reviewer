"""
Library of prompting tools necessary for the agent using the 
ell framework.

This should inject prompts defined in prompts/ rather than
contain its own
"""
import ell

#these should be around somewhere
# ell.init(store="./logdir", autocommit=True)

# OLLAMA_HOST = "http://localhost:11434/v1"
# MODEL = "llama3.1:latest"
# ell.models.ollama.register(OLLAMA_HOST)

def call(model, system, task):
    
    @ell.simple(model=model)
    def _call(system, task):
        return [
            ell.system(system),
            ell.user(task)
        ]
    
    return _call(system,task)
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

#these should be around somewhere
ell.init(store="./logdir", autocommit=True)

# OLLAMA_HOST = "http://localhost:11434/v1"
# MODEL = "llama3.1:latest"
# ell.models.ollama.register(OLLAMA_HOST)

def entry_chat_call(model, system, user, response_format):
    @ell.simple(model=model)
    def _call(system, user):
        return [
            ell.system(system),
            ell.user(user)
        ]
    
    return _call(system,user)

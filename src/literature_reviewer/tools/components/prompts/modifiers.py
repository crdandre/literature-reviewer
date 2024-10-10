"""
These could be prompt additions which can be applied on
a recurring basis to guide outputs.

Such as "Be concise", "Target the writing style to a
technical non-specialist audience", etc.

Just noting this as an idea, not required (yet)
"""

class PromptModifiers():
    def be_concise(importance=10):
        return(
            """
            On a scale of 1 to 10, where 10 is most important,
            You should make this response's conciseness
            {importance} out of 10. 
            """
        )
"""
Contains tools to set the models for i/o of each step.
Useful (maybe) for flexible application of reflection.
"""

from pydantic import BaseModel
from typing import List



class ProcessStep(BaseModel):
    name: str
    subtasks: List[str]
    

class ReviewGenerationRun(BaseModel):
    run_id: int
    steps: List[ProcessStep]
    

class ReflectionProcessDefinition(BaseModel):
    title: str
    objective: str
    steps: List[ProcessStep]
    max_iterations: int
    
    
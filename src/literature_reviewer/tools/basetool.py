"""
Base Class for Tools
All tools must adhere to this interface
"""
from abc import ABC, abstractmethod
from literature_reviewer.agents.components.model_call import ModelInterface
from typing import Any
from pydantic import BaseModel
from pydantic_core import CoreSchema, core_schema

class ToolResponse(BaseModel):
    output: str
    explanation: str

class BaseTool(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        model_interface: ModelInterface
    ):
        self.name = name
        self.description = description
        self.model_interface = model_interface
    
    @abstractmethod
    def use(self, step: Any) -> ToolResponse:
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(cls),
                core_schema.dict_schema(
                    core_schema.str_schema(),
                    core_schema.str_schema(),
                    min_length=2,
                    max_length=2,
                )
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: {
                    "name": instance.name,
                    "description": instance.description
                }
            )
        )
"""
Base Class for Tools
All tools must adhere to this interface
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pydantic import BaseModel, create_model
from pydantic_core import CoreSchema, core_schema
from rich.console import Group
from rich.text import Text
from literature_reviewer.agents.components.model_call import ModelInterface


class ToolResponse(BaseModel):
    output: str #probably has to be a str for response_format purposes
    explanation: str

    def as_rich(self) -> Group:
        content = Group(
            Text("Output:", style="bold"),
            Text(self.output.strip(), style="green"),
        )
        if self.explanation:
            content.renderables.append(Text("\nExplanation:", style="italic"))
            content.renderables.append(Text(self.explanation.strip(), style="yellow"))
        return content
    
    
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
        self.output_schema: Optional[Dict[str, Any]] = None
        self.DynamicOutput: Optional[BaseModel] = None
    
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

    def set_output_schema(self, output_schema: Optional[Dict[str, Any]]):
        self.output_schema = output_schema
        if output_schema:
            self.DynamicOutput = create_model('DynamicOutput', **output_schema)
        else:
            self.DynamicOutput = None

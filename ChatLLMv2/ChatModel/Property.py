import dataclasses

from pydantic.dataclasses import dataclass

from langchain_core.tools import BaseTool


@dataclass
class AdditionalModelProperty:
    llmTools: list[BaseTool] = dataclasses.field(default_factory=lambda: [])

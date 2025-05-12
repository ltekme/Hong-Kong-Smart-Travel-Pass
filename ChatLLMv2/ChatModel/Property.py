from dataclasses import dataclass

from langchain_core.tools import BaseTool

@dataclass
class AdditionalModelProperty:
    llmTools: list[BaseTool] = []

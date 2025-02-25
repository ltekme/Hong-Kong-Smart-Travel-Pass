from langchain_core.tools import BaseTool


class AdditionalModelProperty:
    userProfile: str = ""
    llmTools: list[BaseTool] = []

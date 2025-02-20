from langchain_core.tools import BaseTool


class AdditionalLLMProperty:
    userProfile: str = ""
    llmTools: list[BaseTool] = []

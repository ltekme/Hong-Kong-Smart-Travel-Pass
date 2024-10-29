import os
import typing as t
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from langchain_google_community import GoogleSearchAPIWrapper


class PerformGoogleSearchTool(BaseTool):

    class ToolArgs(BaseModel):
        query: str = Field(
            description="Things to search on google"
        )

    name: str = "Google Search"
    description: str = "Used to perform google search to get recent and relevent information. Can be used to lookup anything"
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, query: str, **kwargs) -> str:
        google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if not google_api_key or not google_cse_id:
            return 'Google API Key or Google CSE ID is not provided. Cannot Perform Google Search'
        search = GoogleSearchAPIWrapper(
            google_api_key=google_api_key,
            google_cse_id=google_cse_id
        )
        return search.run(query)

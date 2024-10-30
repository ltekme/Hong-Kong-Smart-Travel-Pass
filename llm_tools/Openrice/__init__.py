import typing as t
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .caller import OpenriceApi


class OpenricaApiToolBase(BaseTool):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._openrice = OpenriceApi(**kwargs)

    @property
    def openrice(self) -> OpenriceApi:
        return self._openrice


class GetOpenriceRestaurantRecommendationTool(OpenricaApiToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        district_id: t.Optional[int] = Field(
            default=None,
            description="District filter id, default None, can be get from `Get Openrice Filters` tool. Can be used to narrow down restaurant search district. Only input id from district filter into this field."
        )
        landmark_id: t.Optional[int] = Field(
            default=None,
            description="Landmark filter id, default None, can be get from `Get Openrice Filters` tool. Can be used to narrow down restaurant search district. Only input id from landmark filter into this field."
        )
        keyword: t.Optional[str] = Field(
            default=None,
            description="Restaurant search keyword, default None, can be used to narrow down restaurant by keyword, like `dim sum` for dim sum, `bread` for bakery."
        )
        number_of_results: t.Optional[int] = Field(
            default=3,
            description="Number of search results, default 3, can be 1 to 10"
        )
        starting_result_index: t.Optional[int] = Field(
            default=0,
            description="Search result starting index. Can be used to get next results. e.g. number_of_results=10, starting_result_index=0, will return first 10 results - number_of_results=10, starting_result_index=1, will return the next 10 results after the first 10, so on and so forth."
        )
        lang: t.Optional[t.Literal["en", "sc", "tc"]] = Field(
            default="en",
            description="Language of search result, default, en, can be either, en, sc, tc."
        )

    name: str = "Get Openrice Restaurant Recommendation"
    description: str = """Used to get restaurant recommendation from Openrice. Defaults, location Hong Kong, no specific district, no specific landmark.
District filter id and Landmark filter id can both be used to narrow down restaurant search area.
Real-time data from Openrice like the restaurant information(phone, links, ...) can be obtained using this tool.
When no input is provided, general recommendations will be provided."""
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, **kwargs) -> str:
        return [self.openrice.prettify(restaurant) + '\n\n' for restaurant in self.openrice
                .search(
            district_id=kwargs.get('district_id'),
            landmark_id=kwargs.get('landmark_id'),
            keywords=kwargs.get('keyword'),
            count=kwargs.get('number_of_results', 5),
            start=kwargs.get('starting_result_index', 0),
            lang=kwargs.get('lang', 'en')
        )]


class GetOpenriceFilterTool(OpenricaApiToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        place: str = Field(
            description="The place to get openrice filter."
        )

    name: str = "Get Openrice Filters"
    description: str = "Used to get the district or landmark filters if from Openrice. This tool returns a list of landmark id or district id to sbe used in the `Get Openrice Restaurant Recommendation` tool."
    args_schema:  t.Type[BaseModel] = ToolArgs

    def _run(self, place: str, **kwargs) -> str:
        return self.openrice.search_filter(place)

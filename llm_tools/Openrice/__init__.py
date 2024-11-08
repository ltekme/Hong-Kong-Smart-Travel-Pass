import typing as t
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .caller import RestaurantSearchApi


class OpenricaApiToolBase(BaseTool):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._openrice = RestaurantSearchApi(**kwargs)

    @property
    def openrice(self) -> RestaurantSearchApi:
        return self._openrice


class GetOpenriceRestaurantRecommendationTool(OpenricaApiToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        districtIds: t.Optional[list[int]] = Field(
            default=[],
            description="Narrow your search by geographical area. Find restaurants on Hong Kong Island (Central, Causeway Bay), in Kowloon (Tsim Sha Tsui, Mong Kok), the New Territories (Tsuen Wan, Sha Tin), or the Outlying Islands (Lantau, Cheung Chau). Provide a JSON array of district IDs (e.g., [1999, 2999, 3999]). Leave blank or provide an empty array [] for all districts."
        )
        landmarkIds: t.Optional[list[int]] = Field(
            default=[],
            description="Search for restaurants near a specific landmark. Find places to eat near popular attractions like Ocean Park or Hong Kong Disneyland, shopping malls like IFC or Times Square, or transport hubs like Central Station. Provide a JSON array of landmark IDs (e.g., [9319, 7, 18]). Leave blank or provide an empty array [] for all landmarks."
        )
        cuisineIds: t.Optional[list[int]] = Field(
            default=[],
            description="This filter helps you narrow down restaurants based on their culinary style. Options include broad categories like Western, Japanese, and International, as well as more specific regional cuisines like Hong Kong Style, Sichuan, and Vietnamese. Provide a JSON array of cuisine IDs (e.g., [4000, 1004, 2009]). Leave blank or provide an empty array [] for all cuisines. Provide a JSON array of cuisine IDs (e.g., [4000, 1004, 2009]). Leave blank or provide an empty array [] for all cuisines."
        )
        dishIds: t.Optional[list[int]] = Field(
            default=[],
            description="This filter lets you find restaurants serving particular dishes or types of food. Examples include Fine Dining experiences, All-you-can-eat buffets, Omakase menus, Hot Pot, Sushi/Sashimi, Desserts, and more specific items like Ramen, Korean Fried Chicken, or Snake Soup. This filter focuses on the format or kind of food offered. Provide a JSON array of dish IDs (e.g., [1200, 1076, 1001]). Leave blank or provide an empty array [] for all dishes."
        )
        themeIds: t.Optional[list[int]] = Field(
            default=[],
            description="""This filter categorizes restaurants by the dining experience they offer. For example, "Romantic Dining", "Business Dining", "Family Style Dining", "Private Party", and "Group Dining" help users find places suitable for specific occasions or social settings. This filter describes the overall atmosphere or purpose of a dining experience. Provide a JSON array of theme IDs (e.g., [8, 2, 1]). Leave blank or provide an empty array [] for all themes."""
        )
        amenityIds: t.Optional[list[int]] = Field(
            default=[],
            description="""This filter helps you find restaurants with specific features or services. Options like "Steak House", "Dim Sum Restaurant", "Salt & Sugar Reduction Restaurant", "Pet Friendly", and "Food Wise Eateries" allow users to select based on the restaurant's environment, target audience, or health-conscious options. It focuses on the restaurant's attributes or services. Provide a JSON array of amenity IDs (e.g., [1093, 1003, 1001]). Leave blank or provide an empty array [] for all amenities."""
        )
        priceRangeIds: t.Optional[list[int]] = Field(
            default=[],
            description="The IDs correspond to the following ranges: 1 (Below $50), 2 ($51-100), 3 ($101-200), 4 ($201-400), 5 ($401-800), and 6 (Above $801). Provide a JSON array of price range IDs (e.g., [1, 2, 3]) to filter restaurants by price. Leave blank or provide an empty array [] for all price ranges."
        )
        keywords: t.Optional[str] = Field(
            default=None,
            description="Restaurant search keyword, default None, can be used to narrow down restaurant by keyword, like `dim sum` for dim sum, `bread` for bakery."
        )
        number_of_results: t.Optional[int] = Field(
            default=3,
            description="Number of search results, default 3, can be 1 to 10"
        )

    name: str = "Get Openrice Restaurant Recommendation"
    description: str = """Used to get restaurant recommendation from Openrice. When no resault is found an empty list will be returned.
Real-time data from Openrice like the restaurant information(phone, links, ...) can be obtained using this tool.
When no input is provided, general recommendations will be provided.
Use the `Get Openrice Filters` tool to find openrice filter first before using this tool, 
"""
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self,
             landmarkIds: list[int] = [],
             districtIds: list[int] = [],
             cuisineIds: list[int] = [],
             dishIds: list[int] = [],
             themeIds: list[int] = [],
             amenityIds: list[int] = [],
             priceRangeIds: list[int] = [],
             keywords: str = "",
             number_of_results: int = 3,
             **kwargs) -> str:
        return ''.join([self.openrice.to_beautify_string(restaurant) + '\n\n' for restaurant in self.openrice
                        .search(
            landmarkIds,
            districtIds,
            cuisineIds,
            dishIds,
            themeIds,
            amenityIds,
            priceRangeIds,
            keywords,
            count=number_of_results,
        )])


class GetOpenriceFilterTool(OpenricaApiToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        filter_option_find_input: str = Field(
            description="""Used to get avalable filter options from keyword. Enter the keyword of the filter option like 'dim sum' for dish, 'kowloon bay station' for landmark, 'romantic' for theme, 'pet friendly' for amenity, 'below $50' for price range. This tool will return all avaliable filters that match the keyword."""
        )

    name: str = "Get Openrice Filters"
    description: str = "Used to get filter options from Openrice. All avaliable filters can be obtained using this tool. Enter the filter keyword to search for avaliable filters. YOU MUST USE THIS TOOL TO GET AVALABLE FILTERS. THIS TOOL IS REQUIRED TO USE `Get Openrice Restaurant Recommendation` TOOL TO MAKE SURE THE CORRECTNESS OF EACH FILTER ID."
    args_schema:  t.Type[BaseModel] = ToolArgs

    def _run(self, filter_option_find_input: str, **kwargs) -> str:
        return '\n\n'.join([str(doc) for doc in self.openrice.filters.search(filter_option_find_input)])

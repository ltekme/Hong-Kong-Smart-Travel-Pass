import os
import typing as t
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from langchain_google_community import GoogleSearchAPIWrapper

import googlemaps


class PerformGoogleSearchTool(BaseTool):

    class ToolArgs(BaseModel):
        query: str = Field(
            description="Things to search on google"
        )

    name: str = "Google Search"
    description: str = "Used to perform google search to get recent and relevent information. Can be used to lookup anything. If there is somethgin you are not 100% sure, use this to look it up."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, query: str, **kwargs) -> str:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if not google_api_key or not google_cse_id:
            return 'Cannot Perform Google Search'
        search = GoogleSearchAPIWrapper(
            google_api_key=google_api_key,
            google_cse_id=google_cse_id
        )
        return search.run(query)


class ReverseGeocodeConvertionTool(BaseTool):

    class ToolArgs(BaseModel):
        longitude: float = Field(
            description="longitude of the place to be address searched"
        )
        latitude: float = Field(
            description="latitude of the place to be address searched"
        )

    name: str = "Reverse Geocode Search"
    description: str = "Used to get the address or location from longitude, latitude. This tool return string formated addresses that corospond to the longitude, latitude provided."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, latitude: float, longitude: float, **kwargs) -> str:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return "Cannot Perform Reverse Geocode Search"
        maps = googlemaps.Client(key=google_api_key)
        resault = maps.reverse_geocode((latitude, longitude))
        return "\n".join(list(map(lambda a: a['formatted_address'], resault)))


class GetGeocodeFromPlaces(BaseTool):

    class ToolArgs(BaseModel):
        place: str = Field(
            description='Places or location. Best to be address.'
        )

    name: str = "Geocode Search From Address"
    description: str = "Used to get latitude, longitude of the place if exists"
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, place: str, **kwargs) -> t.Tuple[int, int]:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return "Cannot Perform Reverse Geocode Search"
        maps = googlemaps.Client(key=google_api_key)
        geocode_result = maps.geocode(place)
        location = None
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
        if location:
            return location["lat"], location["lng"]
        return None

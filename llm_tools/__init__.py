from google.oauth2.service_account import Credentials

from .Weather import *
from .Openrice import *
from .MTR import *
from .GoogleSearch import *


class LLMTools:

    def __init__(self, credentials: Credentials, verbose=False) -> None:
        self.credentials = credentials
        self.verbose = verbose

    @property
    def all(self):
        return [
            # Hong Kong Observery
            GetWeatherForcastTool(),
            GetCurrentWeatherTempetureTool(),

            # OpenRice
            GetOpenriceRestaurantRecommendationTool(verbose=self.verbose),
            GetOpenriceDistrictFilterListTool(verbose=self.verbose),
            GetOpenriceLandmarkFilterListTool(verbose=self.verbose),

            # MTR
            GetAllMTRStationInfoTool(
                credentials=self.credentials, verbose=self.verbose),
            GetMTRRouteSuggestionTool(
                credentials=self.credentials, verbose=self.verbose),
            GetMTRStationByNameTool(
                credentials=self.credentials, verbose=self.verbose),

            # Google Search
            PerformGoogleSearchTool(),
        ]

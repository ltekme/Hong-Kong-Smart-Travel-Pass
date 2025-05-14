from google.oauth2.service_account import Credentials
from typing import Optional

from .Weather import *
from .Openrice import *
from .MTR import *
from .Google import *


class LLMTools:

    def __init__(self,
                 credentials: t.Optional[Credentials],
                 google_api_key: Optional[str] = "",
                 google_cse_id: Optional[str] = "",
                 verbose: bool = False) -> None:
        self.credentials = credentials
        self.verbose = verbose
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id

    @property
    def all(self) -> list[BaseTool]:
        return self.getall()

    def getall(self) -> list[t.Any]:
        return [
            # Hong Kong Observery
            GetWeatherForcastTool(),
            GetCurrentWeatherTempetureTool(),

            # OpenRice
            GetOpenriceRestaurantRecommendationTool(
                credentials=self.credentials, verbose=self.verbose),
            GetOpenriceFilterTool(
                credentials=self.credentials, verbose=self.verbose),

            # MTR
            GetAllMTRStationInfoTool(
                credentials=self.credentials, verbose=self.verbose),
            GetMTRRouteSuggestionTool(
                credentials=self.credentials, verbose=self.verbose),
            GetMTRStationByNameTool(
                credentials=self.credentials, verbose=self.verbose),

            # Google
            PerformGoogleSearchTool(
                google_cse_id=self.google_cse_id,
                google_api_key=self.google_api_key,
            ),
            ReverseGeocodeConvertionTool(
                google_api_key=self.google_api_key,
            ),
            GetGeocodeFromPlaces(
                google_api_key=self.google_api_key,
            ),
        ]

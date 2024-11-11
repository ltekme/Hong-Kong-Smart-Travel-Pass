import typing as t
from pydantic import BaseModel
from langchain_core.tools import BaseTool

from .ExternalIo import fetch


class WeatherToolBase(BaseTool):

    def print_log(self, msg: str) -> None:
        if self.verbose:
            print("\033[47m\033[34m[Hong Kong Observatory] " +
                  str(msg) +
                  "\033[0m")

    def __init__(self,
                 verbose: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self.verbose = verbose


class GetWeatherForcastTool(WeatherToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        pass

    name: str = "Weather Forcast Tool"
    description: str = "Used to get the current weather in Hong Kong."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, **kwargs) -> str:
        self.print_log("Getting current weather tempecture")
        return "JSON data fetched from hong kong observatory API" + str(fetch(f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"))


class GetCurrentWeatherTempetureTool(WeatherToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        pass

    name: str = "Current Weather Tempeture Tool"
    description: str = "Used to get the current weather from loacation."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, **kwargs) -> str:
        tempectureUrlMapping = {
            "en": "https://rss.weather.gov.hk/rss/CurrentWeather.xml",
            "tc": "https://rss.weather.gov.hk/rss/CurrentWeather_uc.xml"
        }
        self.print_log("Getting weather forcast")
        data = str(fetch(tempectureUrlMapping["en"]))
        desc_start_string = '<description>\n        <![CDATA['
        desc_start_index = data.index(
            desc_start_string) + len(desc_start_string)
        desc_end_index = data[desc_start_index:].index('</description>')
        return str(data[desc_start_index:][:desc_end_index])

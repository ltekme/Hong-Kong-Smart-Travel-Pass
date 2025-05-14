import typing as t
from pydantic import BaseModel
from langchain_core.tools import BaseTool

from .ExternalIo import fetch, logger

class WeatherToolBase(BaseTool):

    def __init__(self,
                 **kwargs):
        super().__init__(**kwargs)


class GetWeatherForcastTool(WeatherToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        pass

    name: str = "Weather_Forcast_Tool"
    description: str = "Used to get the current weather in Hong Kong."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, **kwargs) -> str:
        logger.debug("Getting current weather tempecture")
        return "JSON data fetched from hong kong observatory API" + str(fetch(f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"))


class GetCurrentWeatherTempetureTool(WeatherToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        pass

    name: str = "Current_Weather_Tempeture_Tool"
    description: str = "Used to get the current weather from loacation."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, **kwargs) -> str:
        tempectureUrlMapping = {
            "en": "https://rss.weather.gov.hk/rss/CurrentWeather.xml",
            "tc": "https://rss.weather.gov.hk/rss/CurrentWeather_uc.xml"
        }
        logger.debug("Getting weather forcast")
        data = str(fetch(tempectureUrlMapping["en"]))
        desc_start_string = '<description>\n        <![CDATA['
        desc_start_index = data.index(
            desc_start_string) + len(desc_start_string)
        desc_end_index = data[desc_start_index:].index('</description>')
        return str(data[desc_start_index:][:desc_end_index])

import typing as t
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from google.oauth2.service_account import Credentials

from .caller import MTRApi


class MTRApiToolBase(BaseTool):

    def __init__(self,
                 credentials: t.Optional[Credentials],
                 **kwargs:  dict[str, t.Any],
                 ) -> None:
        super().__init__(**kwargs)
        self._mtr = MTRApi(credentials=credentials, **kwargs)

    @property
    def mtr(self,) -> MTRApi:
        return self._mtr


class GetAllMTRStationInfoTool(MTRApiToolBase):

    def __init__(self,
                 credentials: t.Optional[Credentials],
                 **kwargs):
        super().__init__(credentials=credentials, **kwargs)

    class ToolArgs(BaseModel):
        pass

    name: str = "Get All MTR Station Info"
    description: str = "A tool used to get all mtr stations info, no input needed. This tool return a csv like string."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, **kwargs) -> str:
        return self.mtr.prettify_station(self.mtr.stations)


class GetMTRStationByNameTool(MTRApiToolBase):

    def __init__(self,
                 credentials: t.Optional[Credentials],
                 **kwargs):
        super().__init__(credentials=credentials, **kwargs)

    class ToolArgs(BaseModel):
        name: str = Field(
            description="Name of the MTR Station to search from, can be in English or Chinese. Provide as sccurate name as possible."
        )

    name: str = "Get MTR Station By Name"
    description: str = "A tool used to get mtr station by name, return a csv like string. More then one resautly may come up out of 4. When not sure which, ask the user. A complete list of stations can be obtained from the `Get All MTR Station Info` tool. This tool return a csv like string."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, name: str, **kwargs) -> str:
        resault = self.mtr.get_station_from_station_name(name)
        if not resault:
            return f"No station with name `{name}` were found."
        return self.mtr.prettify_station(resault)


class GetMTRRouteSuggestionTool(MTRApiToolBase):

    def __init__(self,
                 credentials: t.Optional[Credentials],
                 **kwargs):
        super().__init__(credentials=credentials, **kwargs)

    class ToolArgs(BaseModel):
        origin_station_id: int = Field(
            description="ID of the orginating MTR Station, can be either obtained from the `Get MTR Station By Name` tool, or the `Get All MTR Station Info` tool."
        )
        destination_station_id: int = Field(
            description="ID of the destination MTR Station, can be either obtained from the `Get MTR Station By Name` tool, or the `Get All MTR Station Info` tool."
        )

    name: str = "Get MTR Route Suggention"
    description: str = "Used to get route suggestion by MTR, providing the origin and destination station id will resault one or more route option from origin to destination station. This tool return a string description of each route info."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, origin_station_id: int, destination_station_id: int, **kwargs) -> str:
        return self.mtr.get_route_suggestion(origin_station_id, destination_station_id)

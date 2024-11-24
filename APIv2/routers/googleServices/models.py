from pydantic import BaseModel, Field


class geocodeDataModel:

    class Request(BaseModel):
        latitude: float = Field(
            description="latitude of the location to be looked up",
        )
        longitude: float = Field(
            description="longitude of the location to be looked up",
        )

    class Response(BaseModel):
        localtion: str = Field(
            description="location lookup of the given longitude, latitude",
        )

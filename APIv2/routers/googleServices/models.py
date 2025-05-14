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
        location: str = Field(
            description="location lookup of the given longitude, latitude",
        )


class SpeechToTextModel:
    class Request(BaseModel):
        audioData: str = Field(
            description="The base64 audio data",
        )

    class Response(BaseModel):
        message: str = Field(
            description="The transcript of the audio data"
        )

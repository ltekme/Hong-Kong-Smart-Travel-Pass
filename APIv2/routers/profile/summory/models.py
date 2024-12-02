import datetime
from pydantic import BaseModel, Field


class ProfileSummoryRequest:

    class Request(BaseModel):
        accessToken: str = Field(
            description="The facebook access token of a user"
        )

    class Response(BaseModel):
        success: bool = Field(
            description="Weather the summory is generated sucessfully or not"
        )
        summory: str = Field(
            description="The resault summory."
        )


class ProfileSummoryGet:

    class Response(BaseModel):
        summory: str = Field(
            description="The resault summory."
        )
        lastUpdate: datetime.datetime = Field(
            description="The resault summory last updated."
        )

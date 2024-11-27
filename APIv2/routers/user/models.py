from pydantic import BaseModel, Field


class AuthDataModel:

    class Request(BaseModel):
        accessToken: str = Field(
            description="The facebook access token of a user"
        )

    class Response(BaseModel):
        sessionToken: str = Field(
            description="temporary session token for personalized chat",
        )
        expireEpoch: int = Field(
            description="The expire unix time for the session token"
        )


class RequestProfileSummory:

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

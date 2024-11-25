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

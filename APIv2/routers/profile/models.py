from pydantic import BaseModel, Field


class AuthDataModel:

    class Response(BaseModel):
        sessionToken: str = Field(
            description="temporary session token",
        )
        expireEpoch: int = Field(
            description="The expire unix time for the session token"
        )

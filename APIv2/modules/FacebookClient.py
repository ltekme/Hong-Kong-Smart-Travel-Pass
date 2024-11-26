import facebook  # type: ignore
from dataclasses import dataclass


@dataclass
class FacebookUserInfo:
    id: int
    username: str


def getUsernameAndId(accessToken: str) -> FacebookUserInfo:
    graphApi = facebook.GraphAPI(access_token=accessToken, version="2.12")
    facebookProfile = graphApi.get_object(id="me", fields="id,name")  # type: ignore
    username = str(facebookProfile["name"])  # type: ignore
    facebookId = int(facebookProfile["id"])  # type: ignore
    return FacebookUserInfo(facebookId, username)
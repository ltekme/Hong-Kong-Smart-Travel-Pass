import pprint
import base64
import logging
import requests
import facebook  # type: ignore
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class FacebookUserInfo:
    id: int
    username: str


def getUsernameAndId(accessToken: str) -> FacebookUserInfo:
    """
    Get facebook username and id from access token

    :param accessToken: The access token of a given facebook user.

    :return: A new instance of FacebookUserInfo with Id and username populated.
    """
    logger.debug(f"getting username and Id with {accessToken[:10]=}")

    logger.debug("Initializing Grpah API")
    graphApi = facebook.GraphAPI(access_token=accessToken, version="2.12")

    logger.debug("Gathering id and username")
    facebookProfile = graphApi.get_object(id="me", fields="id,name")  # type: ignore

    logger.debug(f"Got user info, {str(facebookProfile["name"])=}, {int(facebookProfile["id"])=}")  # type: ignore
    return FacebookUserInfo(
        username=str(facebookProfile["name"]),  # type: ignore
        facebookId=int(facebookProfile["id"]),  # type: ignore
    )


def getUserProfileDetails(accessToken: str) -> str:
    """
    Get facebook user profile details

    :param accessToken: The access token of a given facebook user.

    :return: A new instance of FacebookUserInfo with Id and username populated.
    """
    logger.debug(f"getting profile details with {accessToken[:10]=}")

    def removeKeysFromFacebookUserProfile(d: dict[str, str]) -> None:
        """
        Process a dictionary to remove specific keys and convert image URLs to base64 data URLs.

        Brought to you by copilot

        :param d: The dictionary to process.
        """
        keys_to_remove: list[str] = []
        for key, value in d.items():
            if key in ["id", "paging"]:
                keys_to_remove.append(key)
            elif key == "full_picture":
                image_url = value
                image_data = requests.get(image_url).content
                image_data_url = "data:image/{};base64,{}".format(
                    str(value).split("?")[0].split(".")[-1],
                    base64.b64encode(image_data).decode()
                )
                d[key] = image_data_url
            elif isinstance(value, dict):
                removeKeysFromFacebookUserProfile(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        removeKeysFromFacebookUserProfile(item)
        for key in keys_to_remove:
            del d[key]

    logger.debug("Initializing Grpah API")
    graphApi = facebook.GraphAPI(access_token=accessToken, version="2.12")

    logger.debug("getting user details")
    profileDetails = graphApi.get_object(  # type: ignore
        id="me",
        fields="posts.limit(10){message,full_picture,place},birthday,gender"
    )

    logger.debug("cleaning user details")
    removeKeysFromFacebookUserProfile(profileDetails)  # type: ignore

    logger.debug("returning beautified user details")
    return pprint.pformat(profileDetails)  # type: ignore

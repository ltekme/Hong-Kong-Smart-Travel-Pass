import facebook
import requests
import base64


class UserProfile():

    _facebook_access_token: str = ""

    @property
    def facebook_access_token(self) -> str:
        raise AttributeError("Access Token is not readable")

    id: str = ""
    name: str = ""

    @classmethod
    def from_facebook_access_token(cls, facebook_access_token: str) -> "UserProfile":
        profile = cls()
        profile._facebook_access_token = facebook_access_token
        try:
            fbProfile = profile.facebook_graph_api.get_object(id="me", fields="id,name")
            profile.id = fbProfile["id"]
            profile.name = fbProfile["name"]
            return profile
        except Exception as e:
            print(f"Failed to get profile {e=}")
            return cls()

    @property
    def facebook_graph_api(self) -> facebook.GraphAPI:
        return facebook.GraphAPI(access_token=self._facebook_access_token, version="2.12")

    def get_user_details(self) -> dict:
        def process_dict(d):
            keys_to_remove = []
            for key, value in d.items():
                if key == "id" or key == "paging":
                    keys_to_remove.append(key)
                elif key == "full_picture":
                    image_url = value
                    image_data = requests.get(image_url).content
                    image_data_url = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
                    d[key] = image_data_url
                elif isinstance(value, dict):
                    process_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            process_dict(item)
            for key in keys_to_remove:
                del d[key]

        try:
            profile_details = self.facebook_graph_api.get_object(
                id="me",
                fields="posts.limit(10){message,full_picture,place},birthday,gender"
            )
            process_dict(profile_details)
            return profile_details
        except Exception as e:
            print(f"Failed to get profile details {e=}")
            return {}

    def __repr__(self) -> str:
        if not self.id and not self.name:
            return "No Profile Defined"
        return f"Facebook Id: {self.id}({self.name})"

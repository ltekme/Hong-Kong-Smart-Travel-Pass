import facebook


class UserProfile():

    _facebook_access_token: str = ""
    id: str = ""
    name: str = ""

    @classmethod
    def from_facebook_access_token(cls, facebook_access_token: str) -> "UserProfile":
        profile = cls()
        profile._facebook_access_token = facebook_access_token
        try:
            fbProfile = profile.facebook_graph.get_object(id="me", fields="id,name")
            profile.id = fbProfile["id"]
            profile.name = fbProfile["name"]
            return profile
        except Exception as e:
            return cls()

    @property
    def facebook_graph(self) -> facebook.GraphAPI:
        return facebook.GraphAPI(access_token=self._facebook_access_token, version="2.12")

    @property
    def facebook_access_token(self) -> str:
        raise AttributeError("Access Token is not readable")

    def __repr__(self) -> str:
        if not self.id and not self.name:
            return "No Profile Defined"
        return f"Facebook Id: {self.id}({self.name})"

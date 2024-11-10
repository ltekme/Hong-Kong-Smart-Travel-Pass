import os
import facebook
import requests
import base64
import json
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import PromptTemplate
from google.oauth2.service_account import Credentials


class UserProfile:
    verbose: bool = False
    id: str = ""
    name: str = ""
    _details: dict = {}
    _summary: str = ""
    _facebook_access_token: str = ""
    _gcp_credentials: Credentials | None = None

    def logger(self, msg: str):
        if self.verbose:
            print(f"\033[47m\033[34m[Facebook Profile] {msg}\033[0m")

    @property
    def facebook_access_token(self) -> str:
        raise AttributeError("Access Token is not readable")

    @classmethod
    def from_facebook_access_token(cls, facebook_access_token: str, gcp_credentials: Credentials | None = None, verbose: bool = False) -> "UserProfile":
        instance = cls()
        instance.verbose = verbose
        instance.logger("Initializing UserProfile from Facebook access token")
        instance._facebook_access_token = facebook_access_token
        if gcp_credentials is not None:
            instance._gcp_credentials = gcp_credentials
        try:
            fb_profile = instance.facebook_graph_api.get_object(id="me", fields="id,name")
            instance.id = fb_profile["id"]
            instance.name = fb_profile["name"]
            instance.logger(f"Profile loaded: {instance.id} ({instance.name})")
        except Exception as e:
            instance.logger(f"Failed to get profile {e=}")
        return instance

    @property
    def credentials(self) -> Credentials:
        raise AttributeError("Credentials are not readable")

    @credentials.setter
    def credentials(self, value: Credentials) -> None:
        self._gcp_credentials = value

    @property
    def facebook_graph_api(self) -> facebook.GraphAPI:
        return facebook.GraphAPI(access_token=self._facebook_access_token, version="2.12")

    def get_details(self, refresh: bool = False) -> dict:
        self.logger("Fetching profile details")
        if self._details and not refresh:
            self.logger("Returning cached profile details")
            return self._details

        self.logger("Forcing refresh of profile details" if refresh else "Details not cached, fetching from Facebook")

        def process_dict(d):
            keys_to_remove = []
            for key, value in d.items():
                if key in ["id", "paging"]:
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
            self.logger("Profile details fetched and processed")
            self._details = profile_details
        except Exception as e:
            self.logger(f"Failed to get profile details {e=}\nReturning empty dict")
            self._details = {}
        return self._details

    def get_summory(self, refresh: bool = False) -> str:
        self.logger("Generating profile summary")
        if self._summary and not refresh:
            self.logger("Returning cached profile summary")
            return self._summary

        self.logger("Forcing refresh of profile summary" if refresh else "No cached summary, generating new summary")

        if self._gcp_credentials is None:
            self.logger("No GCP Credentials, cannot create LLM for summary")
            return "No GCP Credentials, cannot create LLM for summary"

        self.logger("Getting profile details for summary")
        profile_details = self.get_details(refresh)
        if not profile_details:
            self.logger(f"No Profile Details, cannot create summary, {profile_details=}")
            return "No Profile Details, cannot create summary"

        self.logger("Creating LLM for summary")
        llm = ChatVertexAI(
            model="gemini-1.5-pro-002",
            temperature=1,
            max_tokens=8192,
            timeout=None,
            top_p=0.95,
            max_retries=2,
            credentials=self._gcp_credentials,
            project=self._gcp_credentials.project_id,
            region="us-central1",
        )

        self.logger("Creating prompt for LLM")
        prompt = PromptTemplate.from_template("""The following is the facebook profile of {name}. 
Summorise it to the best of you ability.
Guess the personal preferences and interests of {name} based on the profile.
Feel free to make up any details that are not present by making educated guesses based on the profile detials.

Profile of {name}:
<< EOF
{details}
EOF

Output format information guidence:
<< EOF
persons is a male/femail, born on {{Date of brith}}. His Facebook profile reveals a few key interests:
* **{{Interest 1}}:**: {{Elaborate on how getting interest 1 is concluded}}
...{{ More interests and elaborations if any}}

Educated Guesses/Inferences:
* **{{Education Gusses}}** {{Elaborate on how the guess was made}}
...{{ More guesses and elaborations if any}}

Possible Made-up Details (for illustrative purposes):
* {{Elobration of additional details that could be inferred from the profile.}}
...{{ More inferences if any}}
EOF
""")

        model = prompt | llm

        self.logger("Invoking LLM for summary")
        response = model.invoke({
            "name": self.name,
            "details": profile_details,
        })
        self._summary = str(response.content)
        self.logger("Returning profile summary")
        return self._summary

    def save_to_file(self, path: str) -> None:
        if not path:
            raise ValueError("Path is required to save profile")
        self.logger(f"Saving profile to file: {path}")
        if not os.path.exists(os.path.dirname(path)) and path.startswith("./"):
            self.logger(f"Creating directory for file: {os.path.dirname(path)}")
            if os.path.dirname(path):
                os.makedirs(os.path.dirname(path))
        self.logger("Writing profile to file")
        with open(path, "w") as f:
            f.write(json.dumps({
                "id": self.id,
                "name": self.name,
                "details": self.get_details(),
                "summary": self.get_summory(),
            }, indent=4))

    @classmethod
    def load_from_file(cls, path: str) -> "UserProfile":
        if not path:
            raise ValueError("Path is required to load profile")
        instance = cls()
        instance.logger(f"Loading profile from file: {path}")
        if not os.path.exists(path):
            instance.logger(f"File not found: {path}")
            return instance
        instance.logger("Reading profile from file")
        with open(path, "r") as f:
            data = json.load(f)
            if not data or not isinstance(data, dict):
                instance.logger("Failed to read profile data from file")
                return instance
            instance.id = data.get("id", "")
            instance.name = data.get("name", "")
            instance._details = data.get("details", {})
            instance._summary = data.get("summary", "")
        instance.logger("Profile loaded from file")
        return instance

    def __repr__(self) -> str:
        if not self.id and not self.name:
            return "No Profile Defined"
        return f"Facebook Id: {self.id}({self.name})"

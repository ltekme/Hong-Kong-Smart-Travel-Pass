import os
import datetime
import base64
import json

import facebook
import requests
from google.oauth2.service_account import Credentials

from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage


class UserProfile:
    id: str = ""
    name: str = ""
    _details: dict = {}
    _summary: str = ""

    _gcp_credentials: Credentials | None = None
    _facebook_access_token: str = ""

    def logger(self, msg: str):
        if self.verbose:
            print(f"\033[47m\033[34m[Facebook Profile] {msg}\033[0m")

    def __init__(self,
                 save_profile: bool = True,
                 storage_path: str = "./profile_data",
                 gcp_credentials: Credentials | None = None,
                 verbose: bool = False,
                 ) -> None:
        self.gcp_credentials = gcp_credentials
        self.verbose = verbose
        self.storage_path = storage_path
        self.save_profile = save_profile
        if self.save_profile and not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    @property
    def gcp_credentials(self) -> None:
        raise AttributeError("Credentials are not readable")

    @gcp_credentials.setter
    def gcp_credentials(self, value: Credentials | None) -> None:
        self._gcp_credentials = value

    @classmethod
    def from_facebook_access_token(cls,
                                   facebook_access_token: str,
                                   gcp_credentials: Credentials | None = None,
                                   verbose: bool = False,
                                   fetch_summory=True,
                                   use_cache=True
                                   ) -> "UserProfile":
        instance = cls(
            gcp_credentials=gcp_credentials,
            verbose=verbose
        )
        instance.logger("Initializing UserProfile from Facebook access token")
        instance._facebook_access_token = facebook_access_token
        try:
            fb_profile = instance.facebook_graph_api.get_object(id="me", fields="id,name")
            instance.id = fb_profile["id"]
            instance.name = fb_profile["name"]
            instance.logger(f"Profile loaded: {instance.id} ({instance.name})")
        except Exception as e:
            instance.logger(f"Failed to get profile {e=}")
            return instance
        if fetch_summory:
            if use_cache:
                instance.logger("Attempting to get details and summary from saved profile")
                profile_read = instance.read(os.path.join(instance.storage_path, f"{instance.id}.json"))
                if profile_read:
                    instance.logger("Details and summory loaded from file")
                    return instance
                instance.logger("Failed to load details and summory from file")
            instance.get_summory()
            instance.logger("Profile loaded from Facebook")
        return instance

    @property
    def facebook_access_token(self) -> None:
        return None

    @facebook_access_token.setter
    def facebook_access_token(self, value: str) -> None:
        self._facebook_access_token = value
        if self._facebook_access_token:
            self.logger("Facebook Access Token Set. Reloading profile")
        profile = self.from_facebook_access_token(value)
        self.id = profile.id
        self.name = profile.name
        if not self.id:
            self.logger("Failed to load profile from access token")
        if self.save_profile:
            self.logger("Attempting to get details and summary from saved profile")
            profile_read = self.read(os.path.join(self.storage_path, f"{self.id}.json"))
            if profile_read:
                self.logger("Details and summory loaded from file")
                return
            self.logger("Failed to load details and summory from file")
        self.logger("Profile loaded from Facebook")

    @property
    def facebook_graph_api(self) -> facebook.GraphAPI:
        return facebook.GraphAPI(access_token=self._facebook_access_token, version="2.12")

    def get_details(self, refresh: bool = False) -> dict:
        self.logger("Fetching profile details")
        if self._details and not refresh:
            self.logger("Returning cached profile details")
            return self._details

        self.logger("Forcing refresh of profile details" if refresh else "Details not cached")

        if self.save_profile and self.id:
            self.logger("Attempting to get details and summary from saved profile")
            profile_read = self.read(os.path.join(self.storage_path, f"{self.id}.json"))
            if profile_read:
                self.logger("Details loaded from file")
                return self._details

        self.logger("No cached details, fetching from Facebook")

        def process_dict(d):
            keys_to_remove = []
            for key, value in d.items():
                if key in ["id", "paging"]:
                    keys_to_remove.append(key)
                elif key == "full_picture":
                    image_url = value
                    image_data = requests.get(image_url).content
                    image_data_url = f"data:image/{str(value).split("?")
                                                   [0].split(".")[-1]};base64,{base64.b64encode(image_data).decode()}"
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

        self.logger("Parsing details to speerate images")
        picture_data: list[dict] = []

        def process_dict_for_summary(d, parent_key=""):
            keys_to_remove = []
            for key, value in d.items():
                if key == "full_picture":
                    print(value)
                    # image_data_url = f"data:image/jpeg;base64,{value}"
                    picture_data.append({
                        # "type": "image_url",
                        # "image_url": {"url": image_data_url},
                        "type": "media",
                        "data": value.split(",")[1],
                        "mime_type": value.split(";")[0].split(":")[1],
                    })
                    keys_to_remove.append(key)
                elif isinstance(value, dict):
                    process_dict_for_summary(value, parent_key + "." + key if parent_key else key)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            process_dict_for_summary(item, f"{parent_key}.{key}[{i}]")
            for key in keys_to_remove:
                del d[key]

        process_dict_for_summary(profile_details)

        self.logger("Creating LLM for summary")
        llm = ChatVertexAI(
            model="gemini-1.5-pro-002",
            temperature=1,
            max_tokens=8192,
            top_p=0.95,
            max_retries=2,
            credentials=self._gcp_credentials,
            project=self._gcp_credentials.project_id,
            region="us-central1",
        )

        self.logger("Creating prompt for LLM")
        prompt = ChatPromptTemplate(
            [("system", """The following is the facebook profile. 
Summorise it to the best of you ability.
Guess the personal preferences and interests of the profile owner based on the profile.
Feel free to make up any details that are not present by making educated guesses based on the profile detials.

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
"""), MessagesPlaceholder("profile")])

        model = prompt | llm

        self.logger("Invoking LLM for summary")
        response = model.invoke({
            "name": self.name,
            "profile": [HumanMessage(content=[{
                "type": "text",
                "text": "Detials:\n<< EOF\n" + json.dumps(profile_details, indent=4) + "\nEOF Attached images:"
            }] + picture_data)]  # type: ignore
        })
        self._summary = str(response.content)
        self.logger("Returning profile summary")
        return self._summary

    @property
    def as_full_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "details": self.get_details(),
            "summary": self.get_summory(),
            "created_epoch": int(datetime.datetime.now().timestamp())
        }

    def save(self, overide_path: str = "") -> None:
        if not self.id and not overide_path:
            raise ValueError("Cannot save profile without id")
        if not self.save_profile and not overide_path:
            self.logger("Profile saving disabled")
            return
        file_path = os.path.join(self.storage_path, f"{self.id}.json")
        if overide_path:
            file_path = overide_path

        self.logger(f"Saving profile to file: {file_path}, using overide path: {bool(overide_path)=}")

        if not os.path.exists(os.path.dirname(file_path)) and file_path.startswith("./"):
            self.logger(f"Creating directory for file: {os.path.dirname(file_path)}")
            if os.path.dirname(file_path):
                os.makedirs(os.path.dirname(file_path))

        self.logger("Writing profile to file")
        with open(file_path, "w") as f:
            f.write(json.dumps(self.as_full_dict, indent=4))

        self.logger("Profile saved")

    def read(self, file_path: str) -> bool:
        self.logger(f"Reading profile from file: {file_path}")
        if not os.path.exists(file_path):
            self.logger(f"File not found: {file_path}")
            return False
        self.logger("Reading profile from file")
        with open(file_path, "r") as f:
            data = json.load(f)
            self.id = data.get("id", "")
            self.name = data.get("name", "")
            self._details = data.get("details", {})
            self._summary = data.get("summary", "")
        self.logger("Profile loaded")
        return True

    def __repr__(self) -> str:
        if not self.id and not self.name:
            return "No Profile Defined"
        return f"Facebook Id: {self.id}({self.name})"

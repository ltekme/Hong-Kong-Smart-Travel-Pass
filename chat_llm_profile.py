import facebook
import requests
import base64
# import json
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from google.oauth2.service_account import Credentials


class UserProfile():

    def logger(self, msg: str):
        if self.verbose:
            print("\033[47m\033[34m[Facebook Profile] " + str(msg) + "\033[0m")

    verbose: bool = False
    id: str = ""
    name: str = ""
    _details: dict = {}
    _summory: str = ""
    _facebook_access_token: str = ""
    _gcp_credentials: Credentials | None = None

    @property
    def facebook_access_token(self) -> str:
        raise AttributeError("Access Token is not readable")

    @classmethod  # as init
    def from_facebook_access_token(cls,
                                   facebook_access_token: str,
                                   gcp_credentials: Credentials | None = None,
                                   verbose: bool = False,
                                   ) -> "UserProfile":
        this = cls()
        this.verbose = verbose
        this.logger("Initializing UserProfile from Facebook access token")
        this._facebook_access_token = facebook_access_token
        if gcp_credentials is not None:
            this._gcp_credentials = gcp_credentials
        try:
            fbProfile = this.facebook_graph_api.get_object(id="me", fields="id,name")
            this.id = fbProfile["id"]
            this.name = fbProfile["name"]
            this.logger(f"Profile loaded: {this.id} ({this.name})")
            return this
        except Exception as e:
            this.logger(f"Failed to get profile {e=}")
            return this

    @property
    def credentials(self) -> Credentials:
        raise AttributeError("Credentials are not readable")

    @credentials.setter
    def credentials(self, value: Credentials) -> None:
        self._gcp_credentials = value

    @property
    def facebook_graph_api(self) -> facebook.GraphAPI:
        return facebook.GraphAPI(access_token=self._facebook_access_token, version="2.12")

    @property
    def details(self) -> dict:
        self.logger("Fetching profile details")
        if self._details:
            self.logger("Returning cached profile details")
            return self._details

        self.logger("Details not cached, fetching from facebook")

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
            self.logger("Profile details fetched and processed")
            return profile_details
        except Exception as e:
            self.logger(f"Failed to get profile details {e=}\nReturning empty dict")
            return {}

    @property
    def summory(self) -> str:
        self.logger("Generating profile summary")
        if self._summory:
            self.logger("Returning cached profile summary")
            return self._summory

        if self._gcp_credentials is None:
            self.logger("No GCP Credentials, cannot create LLM for summary")
            return "No GCP Credentials, cannot create LLM for summory"

        self.logger(f"Getting profile details for summary")
        profile_details = self.details
        if not profile_details:
            self.logger(f"No Profile Details, cannot create summary, {profile_details=}")
            return "No Profile Details, cannot create summory"

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
        self._summory = str(response.content)
        self.logger("Returning profile summary")
        return self._summory

    def __repr__(self) -> str:
        if not self.id and not self.name:
            return "No Profile Defined"
        return f"Facebook Id: {self.id}({self.name})"

import os
import logging
import typing as t
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    @property
    def googleCSEId(self) -> str | None:
        """Used to perform custom google search for LangChain agents"""
        return os.environ.get("GOOGLE_CSE_ID")

    @property
    def googleApiKey(self) -> str | None:
        """Used to perform Geo location address lookup"""
        return os.environ.get("GOOGLE_API_KEY")

    @property
    def gcpServiceAccountFilePath(self) -> str:
        """The service account path for google services"""
        return os.environ.get("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')

    @property
    def applicationDatabaseURI(self) -> str:
        """The Database URI for the application"""
        return os.environ.get("CHATLLM_DB_URL", 'sqlite:///./chat_data/app.db')

    @property
    def applicationChatLLMMessageAttachmentPath(self) -> str:
        """The local path for where message attachments are stored"""
        return os.environ.get("CHATLLM_ATTACHMENT_URL", "./chat_data/messageAttachment")

    @property
    def azureOpenAIAPIKey(self) -> str | None:
        """The Azure OpenAI API Key"""
        return os.environ.get("AZURE_OPENAI_API_KEY")

    @property
    def azureOpenAIAPIUrl(self) -> str | None:
        """The Azure OpenAI API Url"""
        return os.environ.get("AZURE_OPENAI_API_URL")

    @property
    def azureOpenAIAPIDeploymentName(self) -> str | None:
        """The Azure OpenAI Deployment Name"""
        return os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

    @property
    def azureOpenAIAPIVersion(self) -> str | None:
        """The Azure OpenAI API Version"""
        return os.environ.get("AZURE_OPENAI_API_VERSION")

    @property
    def userSessionExpireInSeconds(self) -> int:
        """How long untill user sesion expire"""
        default = 7200
        try:
            return int(os.environ.get("USER_SESSION_EXPIRE_SECONDS", default))
        except ValueError:
            return default

    @property
    def anonymousUserQouta(self) -> int:
        """How long untill user sesion expire"""
        default = 10
        try:
            return int(os.environ.get("ANONYMOUS_USER_MESSAGE_QOUTER", default))
        except ValueError:
            return default


class ClientCookiesKeys:
    SESSION_TOKEN: t.Final[str] = "sessionToken"


# uvicorn only stdout uvicorn.asgi, uvicorn.access, uvicorn.error
# see site-packages/uvicorn/config.py: 383-393
logger = logging.getLogger("uvicorn.asgi")
settings = Settings()

animals = [
    "alligator",
    "anteater",
    "armadillo",
    "auroch",
    "axolotl",
    "badger",
    "bat",
    "bear",
    "beaver",
    "blobfish",
    "buffalo",
    "camel",
    "chameleon",
    "cheetah",
    "chipmunk",
    "chinchilla",
    "chupacabra",
    "cormorant",
    "coyote",
    "crow",
    "dingo",
    "dinosaur",
    "dog",
    "dolphin",
    "dragon",
    "duck",
    "dumbo octopus",
    "elephant",
    "ferret",
    "fox",
    "frog",
    "giraffe",
    "goose",
    "gopher",
    "grizzly",
    "hamster",
    "hedgehog",
    "hippo",
    "hyena",
    "jackal",
    "jackalope",
    "ibex",
    "ifrit",
    "iguana",
    "kangaroo",
    "kiwi",
    "koala",
    "kraken",
    "lemur",
    "leopard",
    "liger",
    "lion",
    "llama",
    "manatee",
    "mink",
    "monkey",
    "moose",
    "narwhal",
    "nyan cat",
    "orangutan",
    "otter",
    "panda",
    "penguin",
    "platypus",
    "python",
    "pumpkin",
    "quagga",
    "quokka",
    "rabbit",
    "raccoon",
    "rhino",
    "sheep",
    "shrew",
    "skunk",
    "slow loris",
    "squirrel",
    "tiger",
    "turtle",
    "unicorn",
    "walrus",
    "wolf",
    "wolverine",
    "wombat",
]

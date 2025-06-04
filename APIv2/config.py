import os
import logging
import typing as t

from dotenv import load_dotenv, dotenv_values


class Settings:

    useEnvFile = False
    envFilePath = ""

    def __init__(self, envFilePath: t.Optional[str] = None):
        if envFilePath and os.path.exists(envFilePath):
            self.useEnvFile = True
            self.envFilePath = envFilePath
            load_dotenv(envFilePath)

    def getAttr(self, attr: str, default: str = "", checkSystemEnvIfFileValNone: t.Optional[bool] = True) -> str:
        val = None
        if self.useEnvFile:
            val = dotenv_values(self.envFilePath).get(attr)
            if val is not None:
                return val
            if checkSystemEnvIfFileValNone:
                val = os.environ.get(attr)
        if val is None:
            val = default
        return val

    @property
    def googleCSEId(self) -> t.Optional[str]:
        """Used to perform custom google search for LangChain agents"""
        return self.getAttr("GOOGLE_CSE_ID")

    @property
    def googleApiKey(self) -> t.Optional[str]:
        """Used to perform Geo location address lookup"""
        return self.getAttr("GOOGLE_API_KEY")

    @property
    def gcpServiceAccountFilePath(self) -> str:
        """The service account path for google services"""
        return self.getAttr("GCP_AI_SA_CREDENTIAL_PATH", 'gcp_cred-ai.json')

    @property
    def applicationDatabaseURI(self) -> str:
        """The Database URI for the application"""
        return self.getAttr("CHATLLM_DB_URL", 'sqlite:///./chat_data/app.db')

    @property
    def applicationChatLLMMessageAttachmentPath(self) -> str:
        """The local path for where message attachments are stored"""
        return self.getAttr("CHATLLM_ATTACHMENT_URL", "./chat_data/messageAttachment")

    @property
    def azureOpenAIAPIKey(self) -> t.Optional[str]:
        """The Azure OpenAI API Key"""
        return self.getAttr("AZURE_OPENAI_API_KEY")

    @property
    def azureOpenAIAPIUrl(self) -> t.Optional[str]:
        """The Azure OpenAI API Url"""
        return self.getAttr("AZURE_OPENAI_API_URL")

    @property
    def azureOpenAIAPIDeploymentName(self) -> t.Optional[str]:
        """The Azure OpenAI Deployment Name"""
        return self.getAttr("AZURE_OPENAI_DEPLOYMENT_NAME")

    @property
    def azureOpenAIAPIVersion(self) -> t.Optional[str]:
        """The Azure OpenAI API Version"""
        return self.getAttr("AZURE_OPENAI_API_VERSION")

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
settings = Settings(".env")

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

import os
import typing as t

from pydantic.dataclasses import dataclass
# from dotenv import load_dotenv, dotenv_values

from .modules.exception import ConfigurationError


@dataclass
class CognitoConfigMap:
    region: str
    userPoolId: str
    clientId: str

    @property
    def authority(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.userPoolId}"

    @property
    def serverMetadataUrl(self) -> str:
        return f"{self.authority}/.well-known/openid-configuration"


class Settings:
    def getAttr(self, attr: str, default: t.Optional[str] = None) -> str:
        return os.environ.get(attr, default) or ""

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
            return int(self.getAttr("USER_SESSION_EXPIRE_SECONDS", str(default)))
        except ValueError:
            return default

    @property
    def cognitoConfig(self) -> CognitoConfigMap:
        region = self.getAttr("AWS_REGION")
        userPoolId = self.getAttr("COGNITO_USER_POOL_ID")
        clientId = self.getAttr("COGNITO_CLIENT_ID")

        if not region or not userPoolId or not clientId:  # or not clientSecret:
            raise ConfigurationError("Cognito configuration is incomplete. Please set all required environment variables.")

        return CognitoConfigMap(
            region=region,
            userPoolId=userPoolId,
            clientId=clientId,
        )

    @property
    def applicationSecret(self) -> str:
        """Application secret for totp"""
        return self.getAttr("APPLICATION_SECRET", "change_me")


settings = Settings()


def setSettings(setting: Settings) -> None:
    """
    Set the global settings for the application.
    :param setting: The Settings instance to set.
    """
    global settings
    settings = setting


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

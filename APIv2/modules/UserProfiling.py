import logging
from ..dependence import llm
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import HumanMessage


logger = logging.getLogger(__name__)


def generateUserProfileSummory(profileDetails: str) -> str:
    """
    Create a summory of a facebook profile

    :param profileDetails: the profile details of a given facebook user.

    :return: Summory of a user facebook profile.
    """
    logger.debug("Initializing user profile summory generate")

    logger.debug("Creating filtering lc messages")
    pictureData: list[dict[str, str]] = []

    def process_dict_for_summary(d: dict[str, str], parent_key: str = ""):
        """
        Process a dictionary to extract and remove 'full_picture' entries.

        :param d: The dictionary to process.
        :param parent_key: The base key for nested dictionaries (used for recursion).
        """
        keys_to_remove: list[str] = []
        for key, value in d.items():
            if key == "full_picture":
                pictureData.append({
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

    logger.debug(f"creating prompt for details")
    prompt = ChatPromptTemplate(
        [("system", (
            "The following is a facebook profile."
            "Summorise it to the best of you ability."
            "Guess the personal preferences and interests of the profile owner based on the profile."
            "Feel free to make up any details that are not present by making educated guesses based on the profile detials."
            ""
            "Output format information guidence:"
            "<< EOF"
            "persons is a male/femail, born on {{Date of brith}}. His Facebook profile reveals a few key interests:"
            "* **{{Interest 1}}:**: {{Elaborate on how getting interest 1 is concluded}}"
            "...{{ More interests and elaborations if any}}"
            ""
            "Educated Guesses/Inferences:"
            "* **{{Education Gusses}}** {{Elaborate on how the guess was made}}"
            "...{{ More guesses and elaborations if any}}"
            ""
            "Possible Made-up Details (for illustrative purposes):"
            "* {{Elobration of additional details that could be inferred from the profile.}}"
            "...{{ More inferences if any}}"
            "EOF"
        )), MessagesPlaceholder("profile")])

    logger.debug(f"Invkoing LLM for summory")
    promptValue = prompt.invoke({  # type: ignore
        "profile": [HumanMessage(content=[{
            "type": "text",
            "text": "Detials:\n<< EOF\n" + profileDetails + "\nEOF Attached images:"
        }] + pictureData)]  # type: ignore
    })
    response = llm.invoke(promptValue)
    responseContent = response.content  # type: ignore
    if isinstance(responseContent, list):
        return responseContent[0]["text"]  # type: ignore
    return responseContent

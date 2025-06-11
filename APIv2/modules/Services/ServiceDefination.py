def getPermissionName(serviceName: str, action: str) -> str:
    """
    Get the permission name for a specific service and action.

    :param serviceName: The name of the service.
    :param action: The action to get the permission name for.
    :return: The permission name.
    """
    return f"{serviceName}:{action}"


CHATLLM_SERIVCE_NAME = "chatLLM"
CHATLLM_INVOKE = getPermissionName(CHATLLM_SERIVCE_NAME, "invoke")
CHATLLM_RECALL = getPermissionName(CHATLLM_SERIVCE_NAME, "recall")
CHATLLM_CREATE = getPermissionName(CHATLLM_SERIVCE_NAME, "create")


class ServiceActionDefination:
    """
    Mapping of service action to id in database.
    """

    actionIdMap = {
        CHATLLM_INVOKE: 1,
        CHATLLM_RECALL: 2,
        CHATLLM_CREATE: 3,
    }

    @classmethod
    def getId(cls, actionName: str) -> int:
        """
        Get the ID of a service action by its name.
        If unknown, returns 0.

        :param actionName: The name of the service action.
        :return: The ID of the service action.
        """
        return cls.actionIdMap.get(actionName, 0)

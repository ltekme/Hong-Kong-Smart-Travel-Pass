from .Permission import PermissionService

CHATLLM_SERIVCE_NAME = "chatLLM"
CHATLLM_INVOKE = PermissionService.getPermissionName(CHATLLM_SERIVCE_NAME, "invoke")
CHATLLM_RECALL = PermissionService.getPermissionName(CHATLLM_SERIVCE_NAME, "recall")
CHATLLM_CREATE = PermissionService.getPermissionName(CHATLLM_SERIVCE_NAME, "create")

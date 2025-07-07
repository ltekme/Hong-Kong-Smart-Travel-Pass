import os
import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv


def createOpenriceChromaDB() -> None:
    from ChatLLM.Tools.Openrice import caller
    from APIv2.dependence import credentials
    filter = caller.Filters(
        initChroma=True,
        credentials=credentials,
    )
    # this only need to be run once in a life time, no need to run everytime
    len(filter.all)  # type: ignore


def createInitialDatatbaseValues(dbSession: so.Session) -> None:
    from APIv2.modules.Services.User.Role import RoleService
    from APIv2.modules.Services.PermissionAndQuota.Permission import PermissionService
    from APIv2.modules.Services.PermissionAndQuota.Quota import QuotaService

    from APIv2.modules.Services.ServiceDefination import ServiceActionDefination
    from APIv2.modules.Services.ServiceDefination import CHATLLM_INVOKE
    from APIv2.modules.Services.ServiceDefination import CHATLLM_RECALL
    from APIv2.modules.Services.ServiceDefination import CHATLLM_CREATE

    permissionService = PermissionService(dbSession=dbSession)
    qoutaService = QuotaService(dbSession=dbSession)
    roleService = RoleService(
        dbSession=dbSession,
        permissionService=permissionService,
        qoutaService=qoutaService,
    )
    administratorRole = roleService.getOrCreateRole(
        name="administrator",
        description="This role is reserved for administrator.",
    )
    anonymousRole = roleService.getOrCreateRole(
        name="Anonymous",
        description="This role is assigned to anonymous users who do not have an account.",
    )
    authenticatedRole = roleService.getOrCreateRole(
        name="Authenticated",
        description="This role is assigned to anonymous users who do not have an account.",
    )
    recallPermission = permissionService.getOrCreatePermission(
        description="Recall converstation",
        actionId=ServiceActionDefination.getId(CHATLLM_RECALL)
    )
    invokePermission = permissionService.getOrCreatePermission(
        description="Invoke the chat LLM service.",
        actionId=ServiceActionDefination.getId(CHATLLM_INVOKE),
    )
    createPermission = permissionService.getOrCreatePermission(
        description="Create a chat LLM service.",
        actionId=ServiceActionDefination.getId(CHATLLM_CREATE),
    )
    dbSession.commit()

    print("Createing Anymouse Permission and qouta")

    permissionService.createRoleAssociation(
        role=anonymousRole,
        permission=invokePermission,
    )
    permissionService.createRoleAssociation(
        role=anonymousRole,
        permission=createPermission,
    )
    qoutaService.getOrCreateRoleQuota(
        role=anonymousRole,
        actionId=ServiceActionDefination.getId(CHATLLM_CREATE),
        value=1  # Limit to only create 1 conversation per user
    )
    qoutaService.getOrCreateRoleQuota(
        role=anonymousRole,
        actionId=ServiceActionDefination.getId(CHATLLM_INVOKE),
        value=10  # Limit to only 10 message sent
    )
    dbSession.commit()

    print("Createing administratorRole permission and qouta")
    permissionService.createRoleAssociation(
        role=administratorRole,
        permission=invokePermission,
    )
    permissionService.createRoleAssociation(
        role=administratorRole,
        permission=createPermission,
    )
    permissionService.createRoleAssociation(
        role=administratorRole,
        permission=recallPermission,
    )
    qoutaService.getOrCreateRoleQuota(
        role=administratorRole,
        actionId=ServiceActionDefination.getId(CHATLLM_CREATE),
        value=9999  # unlimited
    )
    qoutaService.getOrCreateRoleQuota(
        role=administratorRole,
        actionId=ServiceActionDefination.getId(CHATLLM_INVOKE),
        value=9999  # unlimited
    )
    qoutaService.getOrCreateRoleQuota(
        role=administratorRole,
        actionId=ServiceActionDefination.getId(CHATLLM_RECALL),
        value=9999  # unlimited
    )
    dbSession.commit()

    print("Creating authenticatedRole permission and quota")
    permissionService.createRoleAssociation(
        role=authenticatedRole,
        permission=invokePermission,
    )
    permissionService.createRoleAssociation(
        role=authenticatedRole,
        permission=createPermission,
    )
    permissionService.createRoleAssociation(
        role=authenticatedRole,
        permission=recallPermission,
    )
    qoutaService.getOrCreateRoleQuota(
        role=authenticatedRole,
        actionId=ServiceActionDefination.getId(CHATLLM_CREATE),
        value=3
    )
    qoutaService.getOrCreateRoleQuota(
        role=authenticatedRole,
        actionId=ServiceActionDefination.getId(CHATLLM_INVOKE),
        value=20
    )
    qoutaService.getOrCreateRoleQuota(
        role=authenticatedRole,
        actionId=ServiceActionDefination.getId(CHATLLM_RECALL),
        value=9999
    )
    dbSession.commit()


if __name__ == "__main__":

    load_dotenv('.env')

    print("Creating database tables...")
    from APIv2.modules.ApplicationModel import TableBase
    from APIv2.config import settings

    if settings.applicationDatabaseURI.startswith("sqlite:///"):
        dbFile = settings.applicationDatabaseURI.replace("sqlite:///", "./")
        if not os.path.exists(os.path.dirname(dbFile)):
            os.makedirs(os.path.dirname(dbFile))

    engine = sa.create_engine(url=settings.applicationDatabaseURI)
    TableBase.metadata.create_all(engine)

    print("Database tables created successfully.")
    print("Createing Initial Data")

    createInitialDatatbaseValues(
        dbSession=so.Session(engine, expire_on_commit=False)  # type: ignore
    )
    print("Createing chroma db Data")
    createOpenriceChromaDB()

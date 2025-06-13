import os
import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv


def createInitialDatatbaseValues(dbSession: so.Session) -> None:
    from APIv2.modules.Services.User.Role import RoleService
    from APIv2.modules.Services.PermissionAndQuota.Permission import PermissionService
    from APIv2.modules.Services.PermissionAndQuota.Quota import QuotaService

    from APIv2.modules.Services.ServiceDefination import (
        ServiceActionDefination,
        CHATLLM_INVOKE,
        CHATLLM_CREATE,
    )
    permissionService = PermissionService(dbSession=dbSession)
    qoutaService = QuotaService(dbSession=dbSession)
    roleService = RoleService(
        dbSession=dbSession,
        permissionService=permissionService,
        qoutaService=qoutaService,
    )
    anonymousRole = roleService.getOrCreateRole(
        name="Anonymous",
        description="This role is assigned to anonymous users who do not have an account.",
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

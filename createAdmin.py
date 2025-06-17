import os
import sys
import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv

from APIv2.modules.Services.User.Role import RoleService
from APIv2.modules.Services.User.User import UserService
from APIv2.modules.Services.User.UserRole import UserRoleService
from APIv2.modules.Services.PermissionAndQuota.Permission import PermissionService
from APIv2.modules.Services.PermissionAndQuota.Quota import QuotaService
from APIv2.config import settings


if __name__ == "__main__":

    load_dotenv('.env')
    args = sys.argv
    if len(args) != 2:
        raise Exception("Invalid input format is [createAdmin.py email@example.com]")
    email = args[1]

    if settings.applicationDatabaseURI.startswith("sqlite:///"):
        dbFile = settings.applicationDatabaseURI.replace("sqlite:///", "./")
        if not os.path.exists(os.path.dirname(dbFile)):
            os.makedirs(os.path.dirname(dbFile))

    engine = sa.create_engine(url=settings.applicationDatabaseURI)
    dbSession = so.Session(engine, expire_on_commit=False)

    permissionService = PermissionService(dbSession=dbSession)
    qoutaService = QuotaService(dbSession=dbSession)
    userRoleService = UserRoleService(dbSession=dbSession)
    roleService = RoleService(
        dbSession=dbSession,
        permissionService=permissionService,
        qoutaService=qoutaService,
    )
    userService = UserService(
        dbSession=dbSession,
        roleService=roleService,
        userRoleService=userRoleService
    )

    adminRole = roleService.getByName('administrator')
    if adminRole is None:
        raise Exception("Database is not inited, failed to get admin")
    user = userService.getByEmail(email)
    if not user:
        raise Exception("The user was not found in the database")
    userRoleService.associateUserWithRole(
        user=user,
        role=adminRole,
    )
    dbSession.commit()
    print('Associated user with role')

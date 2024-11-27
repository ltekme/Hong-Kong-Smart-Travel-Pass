from alembic import command
from alembic.config import Config
from APIv2.modules.ApplicationModel import TableBase
from APIv2.dependence import dbEngine

TableBase.metadata.create_all(dbEngine)

alembic_cfg = Config("./alembic.ini")
command.stamp(alembic_cfg, "head")

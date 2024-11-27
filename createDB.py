import os
import logging
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from ChatLLMv2 import DataHandler


logger = logging.getLogger(__name__)

dbUrl = os.environ.get("CHATLLM_DB_URL", "sqlite://")
dbEngine = sa.create_engine(url=dbUrl)

target_metadata = DataHandler.TableBase.metadata
try:
    from APIv2.modules import ApplicationModel
    target_metadata = ApplicationModel.TableBase.metadata
except:
    logger.warning(f"Module ApplicationModel not found. Skipping import.")

target_metadata.create_all(dbEngine)

alembic_cfg = Config("./alembic.ini")
command.stamp(alembic_cfg, "head")

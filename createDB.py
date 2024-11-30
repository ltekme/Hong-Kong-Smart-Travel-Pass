import os
import logging
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from ChatLLMv2 import DataHandler

load_dotenv('.env')

logger = logging.getLogger(__name__)

dbUrl = os.environ.get("CHATLLM_DB_URL", "sqlite:///:memory:")

if dbUrl.startswith("sqlite:///"):
    dbFile = dbUrl.replace("sqlite:///", "./")
    if not os.path.exists(os.path.dirname(dbFile)):
        os.makedirs(os.path.dirname(dbFile))

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

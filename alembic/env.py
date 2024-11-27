import os
import logging
from dotenv import load_dotenv
from sqlalchemy import (
    pool,
    engine_from_config
)
from alembic import context
from ChatLLMv2 import DataHandler

logger = logging.getLogger(__name__)

# The TRY is just to import the tables from APIv2
# This is required so when TableBase.__subclasses__() in ChatLLMv2 is called
# Both classes defined in APIv2.modules.ApplicationModel can be found
# Eventually a better way to do this is needed in the future for expandability
# The 2 component (APIv2, ChatLLMv2) should be seperate but whatever
# This is to allow the APIv2 to be completely not exist yet still work
target_metadata = DataHandler.TableBase.metadata
try:
    from APIv2.modules import ApplicationModel
    target_metadata = ApplicationModel.TableBase.metadata
except:
    logger.warning(f"Module ApplicationModel not found. Skipping import.")

logger.debug(f"List of tables: {target_metadata.tables=}")

load_dotenv(".env")

dbUrl = os.environ.get("CHATLLM_DB_URL", "sqlite://")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=dbUrl,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        configuration={
            "sqlalchemy.url": dbUrl,
            "sqlalchemy.echo": True
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import logging


# uvicorn only stdout uvicorn.asgi, uvicorn.access, uvicorn.error
# see site-packages/uvicorn/config.py: 383-393
logger = logging.getLogger("uvicorn.asgi")


def setLogger(loggerInstance: logging.Logger) -> None:
    """
    Set the global logger for the application.
    :param loggerInstance: The Logger instance to set.
    """
    global logger
    logger = loggerInstance

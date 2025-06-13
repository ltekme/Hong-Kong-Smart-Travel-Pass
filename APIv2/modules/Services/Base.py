import sqlalchemy.orm as so

from ...config import logger


class ServiceBase:
    def __init__(self, dbSession: so.Session, serviceName: str) -> None:
        self.dbSession = dbSession
        self.serviceName = serviceName

    def loggerDebug(self, message: str) -> None:
        """
        Log a debug message with the service name.
        :param message: The message to log.
        """
        logger.debug(f"[{self.serviceName}] {message}")

    def loggerWarning(self, message: str) -> None:
        """
        Log a warning message with the service name.
        :param message: The message to log.
        """
        logger.warning(f"[{self.serviceName}] {message}")

    def loggerInfo(self, message: str) -> None:
        """
        Log an info message with the service name.
        :param message: The message to log.
        """
        logger.info(f"[{self.serviceName}] {message}")

    def loggerError(self, message: str) -> None:
        """
        Log an error message with the service name.
        :param message: The message to log.
        """
        logger.error(f"[{self.serviceName}] {message}")

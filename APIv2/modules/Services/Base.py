import typing as t
import sqlalchemy.orm as so

from APIv2.logger import logger


class ServiceWithLogging:
    def __init__(self, serviceName: str) -> None:
        self.serviceName = serviceName

    def setLoggerAdditionalPrefix(self, prefix: t.Optional[str] = None) -> None:
        """
        Set an additional prefix for the logger.
        :param prefix: The prefix to set.
        """
        if prefix is None:
            self.serviceName = f"[{self.serviceName}]"
            return
        if prefix:
            self.serviceName = f"{self.serviceName}][{prefix}"
            return
        self.serviceName = f"[{self.serviceName}]"

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


class ServiceBase(ServiceWithLogging):
    def __init__(self, dbSession: so.Session, serviceName: str) -> None:
        super().__init__(serviceName)
        self.dbSession = dbSession

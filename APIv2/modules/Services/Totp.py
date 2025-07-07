from pyotp import TOTP

from .Base import ServiceWithLogging
from APIv2.config import settings


class TotpService(ServiceWithLogging):
    def __init__(self) -> None:
        super().__init__("TotpService")

    def verify(self, totp: str) -> bool:
        currentTotp = TOTP(settings.applicationSecret).now()
        self.loggerDebug(f"Verifying TOTP {currentTotp} == {totp}")
        return currentTotp == totp

    @property
    def currentValue(self) -> str:
        return TOTP(settings.applicationSecret).now()

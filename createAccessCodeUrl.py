import pyotp
import qrcode

from APIv2.config import settings

url = pyotp.totp.TOTP(settings.applicationSecret).provisioning_uri(name='HongKongSmartTravelPass', issuer_name='SecureApp')
img = qrcode.make(url)
img.save("./totp.png")  # type: ignore

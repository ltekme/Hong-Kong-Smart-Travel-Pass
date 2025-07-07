import os
import qrcode
import webbrowser
import tkinter as tk

from io import BytesIO
from dotenv import load_dotenv
from PIL import ImageTk, Image

load_dotenv(".env")

if True:
    from APIv2.modules.Services.Totp import TotpService


def getOtp():
    totpService = TotpService()
    return totpService.currentValue

def getLink(otp: str):
    url = os.environ.get("APPLICATION_PUBLIC_URL")
    if url is None:
        raise Exception("Missing url")
    return f"{url}?access_code={otp}"


def getLinkQr(url: str):
    qr_img = qrcode.make(url)
    buf = BytesIO()
    qr_img.save(buf)
    buf.seek(0)
    return buf  # Return BytesIO object

class Data():
    def __init__(self, otp: str = ""):
        self.otp = otp
    @property
    def url(self)-> str:
        return getLink(self.otp)
    def get_qr(self):
        image = ImageTk.PhotoImage(Image.open(getLinkQr(self.url)).resize((256, 256)))
        print(image)
        return image
    
if __name__ == "__main__":
    root = tk.Tk()
    root.config(bg="#d5d5d5")
    root.title('Hong Kong Smart Travel Pass')
    root.geometry("500x200")
    root.resizable(False, False)
    data = Data(getOtp())

    def qrCallback():
        qrWindow = tk.Toplevel(root)
        qrWindow.title(data.otp)
        qrWindow.geometry("256x256")
        img = data.get_qr()
        label = tk.Label(qrWindow, image=img)
        label.image = img #type: ignore
        label.pack()

    viewQr = tk.Button(root, text="Get Link QR code", command=qrCallback)
    viewQr.place(rely=1.0, relx=1.0, x=0, y=0, anchor=tk.SE)
    
    accessCodeLabel = tk.Label(root, text=data.otp)
    accessCodeLabel.pack(pady=0)
    accessCodeLabel.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
    accessCodeLabel.config(font=("Courier", 44))
    accessCodeLabel.bind("<Button-1>", lambda _: webbrowser.open(data.url, new=2))

    def update():
        data.otp = getOtp()
        accessCodeLabel.config(text=data.otp)
        print(f"OTP updated to {data.otp}")
        root.after(1000, update)

    update()
    root.mainloop()
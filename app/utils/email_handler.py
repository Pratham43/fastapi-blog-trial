from email.message import EmailMessage

import aiosmtplib
from fastapi.templating import Jinja2Templates

from app.config import Settings

templates = Jinja2Templates(directory="app/templates")

async def send_email(
    to_email: str,
    subject: str,
    plain_text: str,
    html_content: str | None = None
) -> None:
    message = EmailMessage()
    message["From"] = Settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain_text)
    
    if html_content:    
        message.add_alternative(html_content, subtype="html")
         
    await aiosmtplib.send(
        message,
        hostname=Settings.mail_hostname,
        port=Settings.mail_port,
        username=Settings.mail_username if Settings.mail_username else None,
        password=Settings.mail_password.get_secret_value() or None,
        start_tls=Settings.mail_use_tls,
    )
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
    
    
async def send_password_reset_email(to_email: str, username: str, token: str) -> None:
    reset_url = f"{Settings.frontend_url}/reset-password?token={token}"

    template = templates.env.get_template("email/password_reset.html")
    html_content = template.render(reset_url=reset_url, username=username)

    plain_text = f"""Hi {username},

    You requested to reset your password. Click the link below to set a new password:

    {reset_url}

    This link will expire in 1 hour.

    If you didn't request this, you can safely ignore this email.

    Best regards,
    The ClearDay Blog Team
    """

    await send_email(
        to_email=to_email,
        subject="Reset Your Password - FastAPI Blog",
        plain_text=plain_text,
        html_content=html_content,
    )
import smtplib
import os
import logging
from email.mime.text      import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base      import MIMEBase
from email                import encoders

logger    = logging.getLogger(__name__)
SMTP_HOST = "smtp.company.com"
SMTP_PORT = 25
SMTP_USER = ""
SMTP_PASS = ""

def send_email(to: str, subject: str, body: str, attachment_path: str = None) -> bool:
    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER or "noreply@company.com"
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment; filename=" + os.path.basename(attachment_path)
        )
        msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            if SMTP_USER:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        logger.info("[email] 발송 완료 to=" + to)
        return True
    except Exception as e:
        logger.error("[email] 발송 실패: " + str(e))
        return False

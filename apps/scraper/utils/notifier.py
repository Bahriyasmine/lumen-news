import smtplib
from email.mime.text import MIMEText
import logging
import os

# === Configuration ===
EMAIL_ENABLED = True

# Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "azizbchir189@gmail.com"
SENDER_PASSWORD = "zhlp nigs fcyq elph"
RECEIVER_EMAIL = "mohamedaziz.b'chir@esprit.tn"


def send_email(subject, body):
    """Send an email notification."""
    if not EMAIL_ENABLED:
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logging.info("✅ Email notification sent successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")

def notify(subject, message):
    """Universal notification trigger."""
    send_email(subject, message)

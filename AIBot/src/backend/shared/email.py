import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from src.Backend.core.config import settings


def send_email(
    to_email: str,
    subject: str,
    body: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
) -> bool:
    """
    Send email using SMTP.
    Returns True if successful, False otherwise.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user or "noreply@example.com"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        if smtp_user and smtp_password:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, to_email, text)
            server.quit()
            return True
        else:
            # For development - just log the email
            print(f"EMAIL TO: {to_email}")
            print(f"SUBJECT: {subject}")
            print(f"BODY: {body}")
            return True
            
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email with token."""
    subject = "Password Reset Request"
    body = f"""
    You have requested a password reset.
    
    Use this token to reset your password: {reset_token}
    
    If you did not request this, please ignore this email.
    """
    
    return send_email(email, subject, body)

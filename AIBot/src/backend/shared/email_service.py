import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from src.backend.core.settings import settings


class EmailService:
    """Email service for sending notifications and password resets."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email using SMTP.
        Returns True if successful, False otherwise.
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user or "noreply@fastapi-app.com"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            if self.smtp_user and self.smtp_password:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.smtp_user, to_email, text)
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

    def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email with token."""
        subject = "Password Reset Request"
        
        text_body = f"""
        You have requested a password reset for your account.
        
        Use this token to reset your password: {reset_token}
        
        This token will expire in 1 hour.
        
        If you did not request this, please ignore this email.
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested a password reset for your account.</p>
            <p><strong>Reset Token:</strong> <code>{reset_token}</code></p>
            <p><em>This token will expire in 1 hour.</em></p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, text_body, html_body)

    def send_welcome_email(self, email: str, full_name: str, tenant_name: str) -> bool:
        """Send welcome email to new users."""
        subject = f"Welcome to {settings.PROJECT_NAME}!"
        
        text_body = f"""
        Hello {full_name},
        
        Welcome to {settings.PROJECT_NAME}!
        
        Your account has been created successfully for tenant: {tenant_name}
        
        You can now log in and start using our AI-powered services.
        
        Best regards,
        The {settings.PROJECT_NAME} Team
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Welcome to {settings.PROJECT_NAME}!</h2>
            <p>Hello <strong>{full_name}</strong>,</p>
            <p>Welcome to {settings.PROJECT_NAME}!</p>
            <p>Your account has been created successfully for tenant: <strong>{tenant_name}</strong></p>
            <p>You can now log in and start using our AI-powered services.</p>
            <br>
            <p>Best regards,<br>
            The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, text_body, html_body)


# Global email service instance
email_service = EmailService()

from __future__ import annotations

import random
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.backend.core.settings import settings
from src.backend.shared.email_service import email_service
from . import models
from .schemas import ContactType, OtpPurpose


class MessageCentralProvider:
    """MessageCentral VerifyNow API provider for SMS OTP only."""
    
    def __init__(self):
        self.base_url = "https://cpaas.messagecentral.com"
        self.auth_token = settings.MESSAGECENTRAL_AUTH_TOKEN
    
    def _headers(self) -> dict:
        if not self.auth_token:
            print("[SMS] WARNING: No auth token configured - API calls will fail")
            return {}
        return {
            'authToken': f'{self.auth_token}'
        }

    def _alt_headers(self) -> dict:
        """Alternate header format with authToken as per API requirements."""
        if not self.auth_token:
            return {}
        return {
            'authToken': f'{self.auth_token}'
        }
    
    def send_sms_otp(self, phone_number: str) -> Dict[str, Any]:
        """Send SMS OTP via MessageCentral API."""
        if not self.auth_token:
            print(f"[SMS] DEV MODE - OTP sent to {phone_number}")
            return {"success": True, "verification_id": "dev_sms_123", "timeout": "60"}
        
        # Clean phone number
        clean_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        if clean_number.startswith("91"):
            clean_number = clean_number[2:]
        
        url = f"{self.base_url}/verification/v3/send"
        params = {
            "countryCode": "91",
            "flowType": "SMS", 
            "mobileNumber": clean_number,
            "otpLength": "6"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                # First try with primary header
                headers = self._headers()
                print("[SMS] Headers:", headers)
                print("[SMS] Params:", params)
                resp = client.post(url, params=params, headers=headers)
                # If unauthorized, retry once with alternate Authorization header
          

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("responseCode") == 200:
                        verification_id = data.get("data", {}).get("verificationId")
                        print(f"[SMS] Sent to {phone_number}, ID: {verification_id}")
                        return {
                            "success": True,
                            "verification_id": verification_id,
                            "timeout": data.get("data", {}).get("timeout", "60")
                        }

                print(f"[SMS] API error: {resp.status_code}")
                if resp.status_code == 401:
                    print("[SMS] ERROR: Invalid or missing auth token. Check MESSAGECENTRAL_AUTH_TOKEN in .env")
                try:
                    print("[SMS] Response:", resp.json())
                except Exception:
                    print("[SMS] Response text:", resp.text[:500])
                return {"success": False, "error": f"API error: {resp.status_code}"}
                
        except Exception as e:
            print(f"[SMS] Send error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_otp(self, verification_id: str, otp_code: str) -> Dict[str, Any]:
        """Validate OTP via MessageCentral API."""
        if not self.auth_token:
            return {"success": True, "verified": True}
        
        url = f"{self.base_url}/verification/v3/validateOtp"
        params = {"verificationId": verification_id, "code": otp_code}
        
        try:
            with httpx.Client(timeout=10.0) as client:
                headers = self._headers()
                resp = client.get(url, params=params, headers=headers)
                if resp.status_code == 401:
                    print("[SMS] 401 on validate with authToken, retrying with Authorization: Bearer ...")
                    headers = self._alt_headers()
                    resp = client.get(url, params=params, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("responseCode") == 200:
                        status = data.get("data", {}).get("verificationStatus")
                        verified = status == "VERIFICATION_COMPLETED"
                        print(f"[SMS] Validation: {status}")
                        return {"success": True, "verified": verified}

                print(f"[SMS] Validation failed: {resp.status_code}")
                try:
                    print("[SMS] Response:", resp.json())
                except Exception:
                    print("[SMS] Response text:", resp.text[:500])
                return {"success": False, "error": "Invalid OTP"}
                
        except Exception as e:
            print(f"[SMS] Validation error: {e}")
            return {"success": False, "error": str(e)}

    def send_sms_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send regular SMS message via MessageCentral API."""
        if not self.auth_token:
            print(f"[SMS] DEV MODE - Message sent to {phone_number}: {message}")
            return {"success": True, "message_id": "dev_msg_123"}
        
        # Clean phone number
        clean_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        if clean_number.startswith("91"):
            clean_number = clean_number[2:]
        
        # Correct endpoint for SMS
        url = f"{self.base_url}/verification/v3/send"
        params = {
            "countryCode": "91",
            "flowType": "SMS",
            "type": "SMS",
            "messageType": "TRANSACTIONAL",
            "mobileNumber": clean_number,
            "senderId": "UTOMOB",  # Use predefined sender ID
            "message": message
        }
        
        headers = {"authToken": self.auth_token}  # Add auth header
        
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, params=params, headers=headers)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("responseCode") == 200:
                        print(f"[SMS] Message sent to {phone_number}")
                        return {"success": True, "data": data}
                
                print(f"[SMS] API error: {resp.status_code}")
                print(f"[SMS] Response: {resp.text}")
                return {"success": False, "error": f"API error: {resp.status_code}"}
                
        except Exception as e:
            print(f"[SMS] Message send error: {e}")
            return {"success": False, "error": str(e)}


class OTPService:
    """Unified OTP service - SMS via MessageCentral, Email via custom generation."""
    
    def __init__(self):
        self.sms_provider = MessageCentralProvider()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _generate_email_code(self, digits: int = 6) -> str:
        """Generate OTP code for email (custom logic)."""
        return "".join(str(random.randint(0, 9)) for _ in range(digits))

    def _throttle_check(self, last_sent_at: Optional[datetime]) -> Optional[int]:
        if not last_sent_at:
            return None
        
        # Ensure both datetimes are timezone-aware for comparison
        now = self._now()
        
        # Handle timezone conversion properly
        if last_sent_at.tzinfo is None:
            # Assume UTC for naive datetime from database
            last_sent_at_aware = last_sent_at.replace(tzinfo=timezone.utc)
        else:
            last_sent_at_aware = last_sent_at
        
        delta = now - last_sent_at_aware
        min_interval = timedelta(seconds=settings.OTP_RESEND_INTERVAL_SECONDS)
        if delta < min_interval:
            remaining = int((min_interval - delta).total_seconds())
            return max(remaining, 1)
        return None

    def request_otp(
        self,
        db: Session,
        *,
        contact_type: ContactType,
        contact: str,
        purpose: OtpPurpose,
        tenant_name: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[bool, int]:
        """
        Request OTP using VerifyNow API. Returns (sent, retry_after_seconds).
        """
        # Check throttle
        latest: Optional[models.OtpRequest] = (
            db.query(models.OtpRequest)
            .filter(
                models.OtpRequest.contact_type == contact_type.value,
                models.OtpRequest.contact == contact,
                models.OtpRequest.purpose == purpose.value,
                models.OtpRequest.consumed == False,  # noqa: E712
            )
            .order_by(models.OtpRequest.created_at.desc())
            .first()
        )

        if latest:
            remain = self._throttle_check(latest.last_sent_at)
            if remain is not None:
                return False, remain

        # Create OTP request record
        expires_at = self._now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        req = models.OtpRequest(
            contact_type=contact_type.value,
            contact=contact,
            purpose=purpose.value,
            tenant_name=tenant_name,
            user_id=user_id,
            code="VERIFYNOW_MANAGED",  # VerifyNow manages the OTP
            expires_at=expires_at,
            consumed=False,
            created_at=self._now(),
            last_sent_at=self._now(),
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        # Send OTP based on contact type
        if contact_type == ContactType.email:
            # Email: Custom OTP generation and sending
            code = self._generate_email_code(6)
            req.code = code
            message = f"Your {purpose.value} code for {settings.PROJECT_NAME} is {code}. It expires in {settings.OTP_EXPIRY_MINUTES} minutes."
            subject = f"Your {settings.PROJECT_NAME} verification code"
            sent = email_service.send_email(contact, subject, message)
        else:
            # SMS: MessageCentral VerifyNow API (no custom OTP)
            result = self.sms_provider.send_sms_otp(contact)
            sent = result.get("success", False)
            if sent and result.get("verification_id"):
                req.messagecentral_verification_id = result.get("verification_id")
                req.messagecentral_timeout = result.get("timeout", "60")
        
        db.commit()
        return sent, settings.OTP_RESEND_INTERVAL_SECONDS

    def verify_otp(
        self,
        db: Session,
        *,
        contact_type: ContactType,
        contact: str,
        purpose: OtpPurpose,
        code: str,
        tenant_name: Optional[str] = None,
    ) -> models.OtpRequest:
        """
        Verify the most recent unconsumed OTP for the contact & purpose.
        Returns the OtpRequest row if valid; raises HTTPException otherwise.
        """
        req: Optional[models.OtpRequest] = (
            db.query(models.OtpRequest)
            .filter(
                models.OtpRequest.contact_type == contact_type.value,
                models.OtpRequest.contact == contact,
                models.OtpRequest.purpose == purpose.value,
                models.OtpRequest.consumed == False,  # noqa: E712
            )
            .order_by(models.OtpRequest.created_at.desc())
            .first()
        )
        if not req:
            raise HTTPException(status_code=400, detail="OTP not found. Please request a new code.")

        # Handle timezone comparison properly
        now = self._now()
        expires_at = req.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new code.")

        # Verify OTP based on contact type
        if contact_type == ContactType.email:
            # Email: Validate against our custom generated code
            if req.code != code:
                raise HTTPException(status_code=400, detail="Invalid code. Please try again.")
        else:
            # SMS: Validate via MessageCentral API
            if req.messagecentral_verification_id:
                result = self.sms_provider.validate_otp(req.messagecentral_verification_id, code)
                if not result.get("success") or not result.get("verified"):
                    raise HTTPException(status_code=400, detail="Invalid code. Please try again.")
            else:
                # Development mode fallback
                raise HTTPException(status_code=400, detail="SMS OTP verification not available. Please request a new code.")

        # If tenant gating is provided, ensure match when present
        if tenant_name and req.tenant_name and req.tenant_name != tenant_name:
            raise HTTPException(status_code=400, detail="Invalid tenant for OTP.")

        req.consumed = True
        db.commit()
        db.refresh(req)
        return req


otp_service = OTPService()


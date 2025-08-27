import os
from dotenv import load_dotenv
from src.backend.shared.database_manager import MasterBase, master_engine, MasterSessionLocal
from src.backend.auth.otp_service import OTPService
from src.backend.auth.schemas import ContactType, OtpPurpose

load_dotenv()

def test_otp_flow(contact_type, contact):
    MasterBase.metadata.create_all(bind=master_engine)
    db = MasterSessionLocal()
    service = OTPService()
    
    try:
        # Send OTP
        sent, _ = service.request_otp(
            db,
            contact_type=contact_type,
            contact=contact,
            purpose=OtpPurpose.login,
            tenant_name="test_tenant"
        )
        print(f"OTP sent to {contact}: {sent}")
        
        if sent:
            code = input("Enter OTP: ")
            try:
                req = service.verify_otp(
                    db,
                    contact_type=contact_type,
                    contact=contact,
                    purpose=OtpPurpose.login,
                    code=code,
                    tenant_name="test_tenant"
                )
                print(f"Verification successful! Request ID: {req.id}")
            except Exception as e:
                print(f"Verification failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    # Test with phone
    print("Testing phone OTP...")
    test_otp_flow(ContactType.phone, "9885794107")
    
    # Test with email
    print("\nTesting email OTP...")
    test_otp_flow(ContactType.email, "nftcoinmkt@gmail.com")
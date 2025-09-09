"""
TOTP (Time-based One-Time Password) service for 2FA
"""
import pyotp
import qrcode
import io
import base64
import secrets
from typing import Tuple, List
from app.config import settings


class TOTPService:
    """Service for handling TOTP 2FA operations"""
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a new TOTP secret key"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(secret_key: str, user_email: str, issuer: str = "Traccar") -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret_key).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Generate backup codes for 2FA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    @staticmethod
    def verify_totp_code(secret_key: str, totp_code: str, window: int = 1) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret_key)
        return totp.verify(totp_code, valid_window=window)
    
    @staticmethod
    def get_current_totp_code(secret_key: str) -> str:
        """Get current TOTP code (for testing purposes)"""
        totp = pyotp.TOTP(secret_key)
        return totp.now()
    
    @staticmethod
    def generate_totp_setup(user_email: str, issuer: str = "Traccar") -> Tuple[str, str, List[str]]:
        """Generate complete TOTP setup (secret, QR code, backup codes)"""
        secret_key = TOTPService.generate_secret_key()
        qr_code_url = TOTPService.generate_qr_code(secret_key, user_email, issuer)
        backup_codes = TOTPService.generate_backup_codes()
        
        return secret_key, qr_code_url, backup_codes

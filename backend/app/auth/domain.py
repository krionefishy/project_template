"""
Auth request models.
Frontend encrypts password with RSA public key before sending.
"""
import base64

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    # Base64-encoded RSA-encrypted password from frontend
    encrypted_password: str = Field(..., min_length=1)

    @field_validator("encrypted_password")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        try:
            base64.b64decode(v)
        except Exception as exc:
            raise ValueError("encrypted_password must be valid base64") from exc
        return v

    def decode_encrypted_password(self) -> bytes:
        return base64.b64decode(self.encrypted_password)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)

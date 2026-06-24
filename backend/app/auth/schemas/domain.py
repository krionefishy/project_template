import base64

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    encrypted_password: str = Field(..., min_length=1)

    @field_validator("encrypted_password")
    @classmethod
    def validate_base64(cls, value: str) -> str:
        try:
            base64.b64decode(value)
        except Exception as exc:
            raise ValueError("encrypted_password must be valid base64") from exc
        return value

    def decode_encrypted_password(self) -> bytes:
        return base64.b64decode(self.encrypted_password)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)

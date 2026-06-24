from pydantic import BaseModel


class TokenPairDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PublicKeyDTO(BaseModel):
    public_key: str

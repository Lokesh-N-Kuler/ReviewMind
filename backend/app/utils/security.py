import base64
import datetime
import hashlib
from typing import Optional
import jwt
import bcrypt
from app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

# JWT generation and validation
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None

# Secure Token Encryption / Decryption for GitHub access tokens
def _derive_key() -> bytes:
    return hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()

def encrypt_token(plain_token: str) -> str:
    """XOR-stream encryption with key-hash and base64 encoding."""
    if not plain_token:
        return ""
    key = _derive_key()
    data = plain_token.encode("utf-8")
    encrypted = bytearray(len(data))
    for i in range(len(data)):
        encrypted[i] = data[i] ^ key[i % len(key)]
    return base64.urlsafe_b64encode(bytes(encrypted)).decode("ascii")

def decrypt_token(encrypted_token: str) -> str:
    """Reversible decryption of encrypted token."""
    if not encrypted_token:
        return ""
    try:
        key = _derive_key()
        raw = base64.urlsafe_b64decode(encrypted_token.encode("ascii"))
        decrypted = bytearray(len(raw))
        for i in range(len(raw)):
            decrypted[i] = raw[i] ^ key[i % len(key)]
        return bytes(decrypted).decode("utf-8")
    except Exception:
        return ""

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.app.core.config import get_settings


def _normalize_key(raw: str) -> bytes:
    try:
        key = base64.urlsafe_b64decode(raw + "==")
        if len(key) == 32:
            return key
    except Exception:
        pass
    b = raw.encode("utf-8")
    if len(b) >= 32:
        return b[:32]
    return (b + b"0" * 32)[:32]


def encrypt_secret(plaintext: str) -> str:
    key = _normalize_key(get_settings().app_enc_key)
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    encrypted = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode("utf-8")


def decrypt_secret(payload: str) -> str:
    key = _normalize_key(get_settings().app_enc_key)
    raw = base64.urlsafe_b64decode(payload.encode("utf-8"))
    nonce = raw[:12]
    encrypted = raw[12:]
    cipher = AESGCM(key)
    return cipher.decrypt(nonce, encrypted, None).decode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

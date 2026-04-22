import base64
import hashlib
import secrets

from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken


def normalize_email(value: str) -> str:
    return value.strip().lower()


def generate_api_key():
    return secrets.token_urlsafe(32)


def _fernet():
    raw_key = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    fernet_key = base64.urlsafe_b64encode(raw_key)
    return Fernet(fernet_key)


def encrypt_value(value: str) -> str:
    return _fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str) -> str:
    return _fernet().decrypt(value.encode('utf-8')).decode('utf-8')


def mask_api_key(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return '*' * len(value)
    return f"{'*' * max(len(value) - visible, 0)}{value[-visible:]}"


def safe_decrypt_value(value: str) -> str | None:
    try:
        return decrypt_value(value)
    except InvalidToken:
        return None

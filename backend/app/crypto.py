import os

from cryptography.fernet import Fernet

from .config import settings


def _load_key() -> bytes:
    path = settings.fernet_key_path
    if path.exists():
        return path.read_bytes()
    key = Fernet.generate_key()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key)
    return key


_fernet = Fernet(_load_key())


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()

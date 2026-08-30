import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 32-byte (256-bit) key, base64-encoded in the env var. AESGCM is authenticated encryption -
# it detects ciphertext tampering on decrypt (raises InvalidTag), not just confidentiality.
_KEY_ENV = "DOCUMENT_ENCRYPTION_KEY"
_DEV_DEFAULT_KEY = base64.b64encode(b"dev-only-32-byte-key-change-me!!").decode()


def _get_key() -> bytes:
    key_b64 = os.environ.get(_KEY_ENV, _DEV_DEFAULT_KEY)
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError(f"{_KEY_ENV} must decode to exactly 32 bytes for AES-256, got {len(key)}")
    return key


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encrypt(plaintext: bytes) -> tuple[bytes, bytes]:
    """Returns (nonce, ciphertext_with_tag). Store both - both are needed to decrypt."""
    key = _get_key()
    nonce = os.urandom(12)  # 96-bit nonce, standard for AES-GCM
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data=None)
    return nonce, ciphertext


def decrypt(nonce: bytes, ciphertext: bytes) -> bytes:
    """Raises cryptography.exceptions.InvalidTag if the ciphertext was tampered with or the
    wrong key/nonce is used - GCM authenticates on decrypt, it doesn't silently return garbage."""
    key = _get_key()
    return AESGCM(key).decrypt(nonce, ciphertext, associated_data=None)

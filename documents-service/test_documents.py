import os
import base64
os.environ["DATABASE_URL"] = "sqlite:///./test_documents.db"
os.environ["DOCUMENT_ENCRYPTION_KEY"] = base64.b64encode(b"0" * 32).decode()

import pytest
import crypto
from storage import LocalDiskStorage


# --- crypto: AES-256-GCM ------------------------------------------------

def test_encrypt_decrypt_roundtrip():
    plaintext = b"FIR-2026-0341: full incident report text..."
    nonce, ciphertext = crypto.encrypt(plaintext)
    decrypted = crypto.decrypt(nonce, ciphertext)
    assert decrypted == plaintext


def test_ciphertext_differs_from_plaintext():
    plaintext = b"sensitive investigation record"
    _, ciphertext = crypto.encrypt(plaintext)
    assert plaintext not in ciphertext


def test_two_encryptions_of_same_plaintext_differ():
    # nonce is random per call - same plaintext must not produce identical ciphertext,
    # otherwise an observer could tell two documents are identical without decrypting.
    plaintext = b"same content"
    nonce1, ct1 = crypto.encrypt(plaintext)
    nonce2, ct2 = crypto.encrypt(plaintext)
    assert nonce1 != nonce2
    assert ct1 != ct2


def test_tampered_ciphertext_fails_to_decrypt():
    from cryptography.exceptions import InvalidTag
    plaintext = b"do not alter this evidence record"
    nonce, ciphertext = crypto.encrypt(plaintext)
    tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])  # flip last byte
    with pytest.raises(InvalidTag):
        crypto.decrypt(nonce, tampered)


def test_wrong_nonce_fails_to_decrypt():
    from cryptography.exceptions import InvalidTag
    plaintext = b"evidence"
    nonce, ciphertext = crypto.encrypt(plaintext)
    wrong_nonce = bytes((nonce[0] ^ 0xFF,)) + nonce[1:]
    with pytest.raises(InvalidTag):
        crypto.decrypt(wrong_nonce, ciphertext)


def test_sha256_hex_matches_stdlib_hashlib():
    import hashlib
    data = b"FIR-2026-0341 full text content"
    assert crypto.sha256_hex(data) == hashlib.sha256(data).hexdigest()


def test_sha256_hex_is_deterministic():
    data = b"same content twice"
    assert crypto.sha256_hex(data) == crypto.sha256_hex(data)


def test_sha256_hex_differs_for_different_content():
    assert crypto.sha256_hex(b"version A") != crypto.sha256_hex(b"version B")


# --- storage: local disk backend ----------------------------------------

def test_local_disk_storage_put_get(tmp_path):
    store = LocalDiskStorage(root=str(tmp_path))
    store.put("key1", b"encrypted-blob-bytes")
    assert store.exists("key1") is True
    assert store.get("key1") == b"encrypted-blob-bytes"


def test_local_disk_storage_missing_key(tmp_path):
    store = LocalDiskStorage(root=str(tmp_path))
    assert store.exists("nonexistent") is False


# --- storage: S3 / MinIO backend, verified against a mocked S3 API ------
# No live MinIO/AWS available in this environment - moto mocks the actual boto3 S3 API
# calls, so this genuinely exercises the S3Storage code path (bucket creation, put_object,
# get_object, head_object) rather than skipping it. It does not prove MinIO's specific
# behavior matches AWS S3 in every edge case, only that our client code is correct.

@pytest.fixture
def mocked_s3_env(monkeypatch):
    from moto import mock_aws
    with mock_aws():
        monkeypatch.setenv("S3_BUCKET", "test-documents-bucket")
        monkeypatch.delenv("S3_ENDPOINT_URL", raising=False)
        import boto3
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-documents-bucket")
        yield


def test_s3_storage_put_get(mocked_s3_env):
    from storage import S3Storage
    store = S3Storage()
    store.put("doc-key-1", b"ciphertext bytes here")
    assert store.exists("doc-key-1") is True
    assert store.get("doc-key-1") == b"ciphertext bytes here"


def test_s3_storage_missing_key(mocked_s3_env):
    from storage import S3Storage
    store = S3Storage()
    assert store.exists("does-not-exist") is False

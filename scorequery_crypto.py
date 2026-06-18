# -*- coding: utf-8 -*-
"""Authenticated encryption helpers for ScoreQuery private files."""

from __future__ import annotations

import base64
import getpass
import json
import os
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


PASSPHRASE_ENV = "SCOREQUERY_DATA_PASSPHRASE"
FORMAT = "scorequery-encrypted-json"
VERSION = 1
ALGORITHM = "AES-256-GCM"
KDF_NAME = "PBKDF2-HMAC-SHA256"
KDF_ITERATIONS = 600_000
KEY_BYTES = 32
SALT_BYTES = 16
NONCE_BYTES = 12
ASSOCIATED_DATA = b"scorequery-encrypted-json/v1"


class EncryptionConfigError(RuntimeError):
    """Raised when encryption cannot run safely because key material is missing."""


class DecryptionError(RuntimeError):
    """Raised when encrypted payload validation or authentication fails."""


def _b64encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def get_env_passphrase() -> str | None:
    value = os.environ.get(PASSPHRASE_ENV)
    return value if value else None


def get_passphrase(prompt: str = "ScoreQuery data encryption passphrase: ", *, confirm: bool = False) -> str:
    env_value = get_env_passphrase()
    if env_value:
        return env_value

    first = getpass.getpass(prompt)
    if not first:
        raise EncryptionConfigError(f"{PASSPHRASE_ENV} is not set and no passphrase was entered.")

    if confirm:
        second = getpass.getpass("Confirm passphrase: ")
        if first != second:
            raise EncryptionConfigError("Passphrases did not match.")

    return first


def derive_key(passphrase: str, salt: bytes, iterations: int = KDF_ITERATIONS) -> bytes:
    if iterations < 300_000:
        raise DecryptionError("Encrypted payload uses too few PBKDF2 iterations.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_BYTES,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_bytes(plaintext: bytes, passphrase: str) -> dict[str, Any]:
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    key = derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, ASSOCIATED_DATA)

    return {
        "scorequery_encrypted": True,
        "format": FORMAT,
        "version": VERSION,
        "algorithm": ALGORITHM,
        "kdf": {
            "name": KDF_NAME,
            "iterations": KDF_ITERATIONS,
            "salt": _b64encode(salt),
        },
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
    }


def decrypt_bytes(payload: dict[str, Any], passphrase: str) -> bytes:
    if not payload.get("scorequery_encrypted") or payload.get("format") != FORMAT:
        raise DecryptionError("Payload is not a ScoreQuery encrypted file.")
    if payload.get("version") != VERSION or payload.get("algorithm") != ALGORITHM:
        raise DecryptionError("Unsupported encrypted payload version or algorithm.")

    kdf = payload.get("kdf") or {}
    if kdf.get("name") != KDF_NAME:
        raise DecryptionError("Unsupported key derivation function.")

    try:
        iterations = int(kdf["iterations"])
        salt = _b64decode(kdf["salt"])
        nonce = _b64decode(payload["nonce"])
        ciphertext = _b64decode(payload["ciphertext"])
    except Exception as exc:
        raise DecryptionError("Encrypted payload is malformed.") from exc

    try:
        key = derive_key(passphrase, salt, iterations)
        return AESGCM(key).decrypt(nonce, ciphertext, ASSOCIATED_DATA)
    except InvalidTag as exc:
        raise DecryptionError("Wrong passphrase or encrypted file has been modified.") from exc


def encrypt_json(data: Any, passphrase: str) -> dict[str, Any]:
    plaintext = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return encrypt_bytes(plaintext, passphrase)


def decrypt_json(payload: dict[str, Any], passphrase: str) -> Any:
    plaintext = decrypt_bytes(payload, passphrase)
    return json.loads(plaintext.decode("utf-8"))


def write_encrypted_json(path: str | os.PathLike[str], data: Any, passphrase: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = encrypt_json(data, passphrase)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_encrypted_json(path: str | os.PathLike[str], passphrase: str) -> Any:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return decrypt_json(payload, passphrase)

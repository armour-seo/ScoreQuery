# -*- coding: utf-8 -*-
"""Encrypt or decrypt local ScoreQuery private files.

Examples:
  python secure_files.py scan
  python secure_files.py encrypt config.json docs/data.json
  python secure_files.py encrypt --delete-plain "*.xlsx"
  python secure_files.py decrypt docs/data.enc.json --output-dir restored
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

from scorequery_crypto import decrypt_bytes, encrypt_bytes, get_passphrase


DEFAULT_PATTERNS = [
    "config.json",
    "docs/data.json",
    "*.xls",
    "*.xlsx",
    "*.xlsm",
    "*.docx",
]


def default_encrypted_path(path: Path) -> Path:
    if path.name == "data.json":
        return path.with_name("data.enc.json")
    if path.name == "config.json":
        return path.with_name("config.enc.json")
    return path.with_name(path.name + ".enc")


def expand_targets(patterns: list[str]) -> list[Path]:
    targets: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        matches = glob.glob(pattern)
        if not matches:
            candidate = Path(pattern)
            if candidate.exists():
                matches = [pattern]
        for match in matches:
            path = Path(match)
            if path.is_file() and path not in seen:
                targets.append(path)
                seen.add(path)
    return targets


def encrypt_file(path: Path, passphrase: str, *, delete_plain: bool, force: bool) -> Path:
    output_path = default_encrypted_path(path)
    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} already exists. Use --force to overwrite.")

    payload = encrypt_bytes(path.read_bytes(), passphrase)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if delete_plain:
        path.unlink()

    return output_path


def decrypt_file(path: Path, passphrase: str, output_dir: Path | None, *, force: bool) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    plaintext = decrypt_bytes(payload, passphrase)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / restored_name(path)
    else:
        output_path = path.with_name(restored_name(path))

    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} already exists. Use --force to overwrite.")

    output_path.write_bytes(plaintext)
    return output_path


def restored_name(path: Path) -> str:
    name = path.name
    if name == "data.enc.json":
        return "data.json"
    if name == "config.enc.json":
        return "config.json"
    if name.endswith(".enc"):
        return name[:-4]
    return name + ".decrypted"


def scan_sensitive_files() -> int:
    hits = expand_targets(DEFAULT_PATTERNS)
    if not hits:
        print("No plaintext private files found by default patterns.")
        return 0

    print("Plaintext private files found:")
    for path in hits:
        print(f"  {path}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Encrypt/decrypt ScoreQuery private files.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser("scan", help="List plaintext private files.")
    scan_parser.set_defaults(func=lambda _args: scan_sensitive_files())

    enc = sub.add_parser("encrypt", help="Encrypt files with AES-256-GCM.")
    enc.add_argument("paths", nargs="+", help="Files or glob patterns to encrypt.")
    enc.add_argument("--delete-plain", action="store_true", help="Delete plaintext files after encryption.")
    enc.add_argument("--force", action="store_true", help="Overwrite existing encrypted files.")

    dec = sub.add_parser("decrypt", help="Decrypt encrypted files.")
    dec.add_argument("paths", nargs="+", help="Encrypted files or glob patterns to decrypt.")
    dec.add_argument("--output-dir", type=Path, help="Directory for restored plaintext files.")
    dec.add_argument("--force", action="store_true", help="Overwrite restored files.")

    args = parser.parse_args()
    if hasattr(args, "func"):
        return args.func(args)

    targets = expand_targets(args.paths)
    if not targets:
        print("No matching files.")
        return 1

    passphrase = get_passphrase(confirm=args.command == "encrypt")

    if args.command == "encrypt":
        for target in targets:
            output = encrypt_file(target, passphrase, delete_plain=args.delete_plain, force=args.force)
            suffix = " and deleted plaintext" if args.delete_plain else ""
            print(f"Encrypted {target} -> {output}{suffix}")
        if args.delete_plain:
            print("Note: normal deletion is not guaranteed secure on SSD/cloud-synced storage.")
        return 0

    if args.command == "decrypt":
        for target in targets:
            output = decrypt_file(target, passphrase, args.output_dir, force=args.force)
            print(f"Decrypted {target} -> {output}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from supabase import Client, create_client


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _enabled() -> bool:
    return bool(_env("SUPABASE_URL") and _env("SUPABASE_SERVICE_ROLE_KEY"))


def _log(message: str) -> None:
    print(f"[supabase-auth] {message}", flush=True)


def _client() -> Client:
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return create_client(url, key)


def _bucket_name() -> str:
    return _env("SUPABASE_STORAGE_BUCKET", "nanobot-private")


def _object_path() -> str:
    return _env("SUPABASE_AUTH_OBJECT", "whatsapp-auth/auth.zip")


def _auth_dir() -> Path:
    return Path(_env("AUTH_DIR", "/app/data/whatsapp-auth"))


def _ensure_bucket(client: Client) -> None:
    bucket = _bucket_name()
    existing = client.storage.list_buckets()
    for item in existing:
        name = getattr(item, "name", None)
        if name is None and isinstance(item, dict):
            name = item.get("name")
        if name == bucket:
            return
    client.storage.create_bucket(bucket, options={"public": False})
    _log(f"created bucket '{bucket}'")


def restore_auth() -> int:
    if not _enabled():
        _log("skipping restore because Supabase Storage is not configured")
        return 0

    auth_dir = _auth_dir()
    auth_dir.mkdir(parents=True, exist_ok=True)
    client = _client()
    bucket = _bucket_name()
    object_path = _object_path()

    try:
        blob = client.storage.from_(bucket).download(object_path)
    except Exception as exc:  # noqa: BLE001
        _log(f"no remote auth backup found at '{bucket}/{object_path}': {exc}")
        return 0

    with tempfile.TemporaryDirectory(prefix="wa-auth-restore-") as temp_dir:
        archive_path = Path(temp_dir) / "auth.zip"
        archive_path.write_bytes(blob)

        restored_dir = Path(temp_dir) / "restored"
        shutil.unpack_archive(str(archive_path), str(restored_dir), "zip")

        if auth_dir.exists():
            shutil.rmtree(auth_dir)
        shutil.copytree(restored_dir, auth_dir)

    _log(f"restored auth from '{bucket}/{object_path}'")
    return 0


def backup_auth() -> int:
    if not _enabled():
        _log("skipping backup because Supabase Storage is not configured")
        return 0

    auth_dir = _auth_dir()
    if not auth_dir.exists():
        _log(f"skipping backup because auth dir does not exist: {auth_dir}")
        return 0

    if not any(auth_dir.iterdir()):
        _log(f"skipping backup because auth dir is empty: {auth_dir}")
        return 0

    client = _client()
    _ensure_bucket(client)
    bucket = _bucket_name()
    object_path = _object_path()

    with tempfile.TemporaryDirectory(prefix="wa-auth-backup-") as temp_dir:
        archive_base = Path(temp_dir) / "auth"
        archive_path = Path(shutil.make_archive(str(archive_base), "zip", root_dir=auth_dir))

        with archive_path.open("rb") as handle:
            client.storage.from_(bucket).upload(
                path=object_path,
                file=handle,
                file_options={"content-type": "application/zip", "upsert": "true"},
            )

    _log(f"uploaded auth backup to '{bucket}/{object_path}'")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"restore", "backup"}:
        print("usage: supabase_auth_sync.py [restore|backup]", file=sys.stderr)
        return 2

    if argv[1] == "restore":
        return restore_auth()
    return backup_auth()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

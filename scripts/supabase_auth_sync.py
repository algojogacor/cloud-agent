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
    print(f"[supabase-sync] {message}", flush=True)


def _client() -> Client:
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return create_client(url, key)


def _bucket_name() -> str:
    return _env("SUPABASE_STORAGE_BUCKET", "nanobot-private")


def _object_path() -> str:
    return _env("SUPABASE_WORKSPACE_OBJECT", "nanobot/workspace.zip")


def _sync_root() -> Path:
    return Path(_env("SUPABASE_SYNC_ROOT", "/app/data"))


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


def _safe_remove_dir(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def restore_workspace() -> int:
    if not _enabled():
        _log("skipping restore because Supabase Storage is not configured")
        return 0

    sync_root = _sync_root()
    sync_root.mkdir(parents=True, exist_ok=True)
    client = _client()
    bucket = _bucket_name()
    object_path = _object_path()

    try:
        blob = client.storage.from_(bucket).download(object_path)
    except Exception as exc:  # noqa: BLE001
        _log(f"no remote workspace backup found at '{bucket}/{object_path}': {exc}")
        return 0

    with tempfile.TemporaryDirectory(prefix="workspace-restore-") as temp_dir:
        archive_path = Path(temp_dir) / "workspace.zip"
        archive_path.write_bytes(blob)

        restored_dir = Path(temp_dir) / "restored"
        shutil.unpack_archive(str(archive_path), str(restored_dir), "zip")

        _safe_remove_dir(sync_root)
        for item in restored_dir.iterdir():
            target = sync_root / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    _log(f"restored workspace from '{bucket}/{object_path}'")
    return 0


def backup_workspace() -> int:
    if not _enabled():
        _log("skipping backup because Supabase Storage is not configured")
        return 0

    sync_root = _sync_root()
    if not sync_root.exists():
        _log(f"skipping backup because sync root does not exist: {sync_root}")
        return 0

    if not any(sync_root.iterdir()):
        _log(f"skipping backup because sync root is empty: {sync_root}")
        return 0

    client = _client()
    _ensure_bucket(client)
    bucket = _bucket_name()
    object_path = _object_path()

    with tempfile.TemporaryDirectory(prefix="workspace-backup-") as temp_dir:
        archive_base = Path(temp_dir) / "workspace"
        archive_path = Path(
            shutil.make_archive(str(archive_base), "zip", root_dir=sync_root)
        )

        with archive_path.open("rb") as handle:
            client.storage.from_(bucket).upload(
                path=object_path,
                file=handle,
                file_options={"content-type": "application/zip", "upsert": "true"},
            )

    _log(f"uploaded workspace backup to '{bucket}/{object_path}'")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"restore", "backup"}:
        print("usage: supabase_auth_sync.py [restore|backup]", file=sys.stderr)
        return 2

    if argv[1] == "restore":
        return restore_workspace()
    return backup_workspace()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

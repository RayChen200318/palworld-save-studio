from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable, Iterable, Mapping


BACKUP_FOLDER_NAME = "Palworld-Save-Studio-Backup"


class SaveTransactionError(RuntimeError):
    """Raised when a staged save cannot be committed as one transaction."""


@dataclass(frozen=True)
class SaveTransactionResult:
    backup_path: str | None
    verified: bool
    files_written: int
    source_verified: bool
    files_changed: tuple[str, ...]
    files_skipped: tuple[str, ...]


SourceManifest = dict[str, dict[str, Any]]


def _safe_relative_path(relative_path: Path) -> Path:
    relative_path = Path(relative_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise SaveTransactionError(f"Unsafe save path: {relative_path}")
    return relative_path


def _fingerprint(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"Size": path.stat().st_size, "Sha256": digest.hexdigest()}


def core_save_paths(save_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for filename in ("Level.sav", "LevelMeta.sav", "WorldOption.sav"):
        path = save_root / filename
        if path.is_file():
            paths.append(Path(filename))

    players = save_root / "Players"
    if players.is_dir():
        for path in sorted(players.rglob("*")):
            if path.is_symlink():
                raise SaveTransactionError(
                    f"Symlinks are not allowed in the Players directory: {path.name}"
                )
            if path.is_file():
                paths.append(path.relative_to(save_root))
    return tuple(paths)


def capture_source_manifest(save_root: Path) -> SourceManifest:
    return {
        relative_path.as_posix(): _fingerprint(save_root / relative_path)
        for relative_path in core_save_paths(save_root)
    }


def source_manifest_matches(save_root: Path, expected: Mapping[str, Any]) -> bool:
    try:
        return capture_source_manifest(save_root) == dict(expected)
    except (OSError, SaveTransactionError):
        return False


def _copy_originals(
    save_root: Path,
    destination: Path,
    relative_paths: Iterable[Path],
) -> set[Path]:
    existing: set[Path] = set()
    for relative_path in relative_paths:
        relative_path = _safe_relative_path(relative_path)
        source = save_root / relative_path
        if not source.is_file():
            continue
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        existing.add(relative_path)
    return existing


def create_persistent_backup(
    save_root: Path,
    relative_paths: Iterable[Path],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    backup_path = save_root / BACKUP_FOLDER_NAME / timestamp
    backup_path.mkdir(parents=True, exist_ok=False)
    try:
        backup_paths = {_safe_relative_path(path) for path in relative_paths}
        players_path = save_root / "Players"
        if players_path.is_dir():
            backup_paths.update(
                path.relative_to(save_root)
                for path in players_path.rglob("*")
                if path.is_file() and not path.is_symlink()
            )
        copied = _copy_originals(save_root, backup_path, backup_paths)
        manifest = {
            "SchemaVersion": 1,
            "CreatedAt": datetime.now(timezone.utc).isoformat(),
            **dict(metadata or {}),
            "Files": {
                path.as_posix(): _fingerprint(backup_path / path)
                for path in sorted(copied)
            },
        }
        (backup_path / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(backup_path, ignore_errors=True)
        raise
    return backup_path


def replace_staged_files(
    *,
    save_root: Path,
    staged_root: Path,
    transaction_root: Path,
    relative_paths: Iterable[Path],
    backup_enabled: bool,
    verify: Callable[[], bool],
    backup_paths: Iterable[Path] | None = None,
    backup_metadata: Mapping[str, Any] | None = None,
    files_skipped: Iterable[Path] = (),
    pre_write_check: Callable[[], bool] | None = None,
) -> SaveTransactionResult:
    """Replace staged files atomically, or create a verified backup-only transaction."""

    paths = tuple(dict.fromkeys(_safe_relative_path(Path(path)) for path in relative_paths))
    if not paths and not backup_enabled:
        raise SaveTransactionError("No staged save files were provided.")
    for relative_path in paths:
        if not (staged_root / relative_path).is_file():
            raise SaveTransactionError(f"Missing staged file: {relative_path}")

    backup_path: Path | None = None
    requested_backup_paths = tuple(
        dict.fromkeys(
            _safe_relative_path(Path(path))
            for path in (backup_paths if backup_paths is not None else paths)
        )
    )
    if backup_enabled:
        try:
            backup_path = create_persistent_backup(
                save_root,
                requested_backup_paths,
                metadata=backup_metadata,
            )
        except Exception as exc:
            raise SaveTransactionError(f"Backup creation failed: {exc}") from exc

    rollback_root = transaction_root / "rollback"
    rollback_root.mkdir(parents=True, exist_ok=True)
    original_paths = _copy_originals(save_root, rollback_root, paths)
    replaced: list[Path] = []

    try:
        if backup_path is not None:
            for relative_path in requested_backup_paths:
                source = save_root / relative_path
                backup = backup_path / relative_path
                if not source.is_file() or not backup.is_file():
                    raise SaveTransactionError(
                        f"Backup verification failed for {relative_path}. No files were written."
                    )
                if _fingerprint(source) != _fingerprint(backup):
                    raise SaveTransactionError(
                        f"Backup verification failed for {relative_path}. No files were written."
                    )
        if pre_write_check is not None and not pre_write_check():
            raise SaveTransactionError(
                "The source save changed while the backup was being created. "
                "No files were written; reload the save before editing again."
            )
        for relative_path in paths:
            target = save_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_root / relative_path, target)
            replaced.append(relative_path)

        if not verify():
            raise SaveTransactionError("Reloaded save did not match the in-memory draft.")
    except Exception as exc:
        rollback_errors: list[str] = []
        for relative_path in reversed(replaced):
            target = save_root / relative_path
            try:
                if relative_path in original_paths:
                    os.replace(rollback_root / relative_path, target)
                elif target.exists():
                    target.unlink()
            except Exception as rollback_exc:
                rollback_errors.append(f"{relative_path}: {rollback_exc}")
        if rollback_errors:
            raise SaveTransactionError(
                f"Commit failed ({exc}); rollback also failed: {'; '.join(rollback_errors)}"
            ) from exc
        if isinstance(exc, SaveTransactionError):
            raise
        raise SaveTransactionError(f"Commit failed and was rolled back: {exc}") from exc

    return SaveTransactionResult(
        backup_path=str(backup_path) if backup_path else None,
        verified=True,
        files_written=len(paths),
        source_verified=True,
        files_changed=tuple(path.as_posix() for path in paths),
        files_skipped=tuple(
            _safe_relative_path(Path(path)).as_posix() for path in files_skipped
        ),
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import shutil
from typing import Callable, Iterable


BACKUP_FOLDER_NAME = "Palworld-Save-Studio-Backup"


class SaveTransactionError(RuntimeError):
    """Raised when a staged save cannot be committed as one transaction."""


@dataclass(frozen=True)
class SaveTransactionResult:
    backup_path: str | None
    verified: bool
    files_written: int


def _copy_originals(
    save_root: Path,
    destination: Path,
    relative_paths: Iterable[Path],
) -> set[Path]:
    existing: set[Path] = set()
    for relative_path in relative_paths:
        source = save_root / relative_path
        if not source.is_file():
            continue
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        existing.add(relative_path)
    return existing


def create_persistent_backup(save_root: Path, relative_paths: Iterable[Path]) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    backup_path = save_root / BACKUP_FOLDER_NAME / timestamp
    backup_path.mkdir(parents=True, exist_ok=False)
    try:
        backup_paths = set(relative_paths)
        players_path = save_root / "Players"
        if players_path.is_dir():
            backup_paths.update(path.relative_to(save_root) for path in players_path.glob("*.sav"))
        _copy_originals(save_root, backup_path, backup_paths)
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
) -> SaveTransactionResult:
    """Atomically replace a fixed set of save files and restore all originals on failure."""

    paths = tuple(dict.fromkeys(Path(path) for path in relative_paths))
    if not paths:
        raise SaveTransactionError("No staged save files were provided.")
    for relative_path in paths:
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise SaveTransactionError(f"Unsafe staged path: {relative_path}")
        if not (staged_root / relative_path).is_file():
            raise SaveTransactionError(f"Missing staged file: {relative_path}")

    backup_path: Path | None = None
    if backup_enabled:
        try:
            backup_path = create_persistent_backup(save_root, paths)
        except Exception as exc:
            raise SaveTransactionError(f"Backup creation failed: {exc}") from exc

    rollback_root = transaction_root / "rollback"
    rollback_root.mkdir(parents=True, exist_ok=True)
    original_paths = _copy_originals(save_root, rollback_root, paths)
    replaced: list[Path] = []

    try:
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
    )

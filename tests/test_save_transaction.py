import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from palworld_save_studio.core.save_transaction import (
    BACKUP_FOLDER_NAME,
    SaveTransactionError,
    capture_source_manifest,
    core_save_paths,
    replace_staged_files,
    source_manifest_matches,
)


class SaveTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.save_root = self.root / "save"
        self.stage_root = self.root / "transaction" / "staged"
        self.transaction_root = self.root / "transaction"
        (self.save_root / "Players").mkdir(parents=True)
        (self.stage_root / "Players").mkdir(parents=True)
        self.paths = [Path("Level.sav"), Path("Players/ABC.sav")]
        (self.save_root / "Level.sav").write_bytes(b"old-level")
        (self.save_root / "Players/ABC.sav").write_bytes(b"old-player")
        (self.stage_root / "Level.sav").write_bytes(b"new-level")
        (self.stage_root / "Players/ABC.sav").write_bytes(b"new-player")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_commit_without_persistent_backup(self) -> None:
        result = replace_staged_files(
            save_root=self.save_root,
            staged_root=self.stage_root,
            transaction_root=self.transaction_root,
            relative_paths=self.paths,
            backup_enabled=False,
            verify=lambda: True,
        )

        self.assertTrue(result.verified)
        self.assertIsNone(result.backup_path)
        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"new-level")
        self.assertFalse((self.save_root / BACKUP_FOLDER_NAME).exists())

    def test_commit_creates_persistent_backup(self) -> None:
        (self.save_root / "Players/UNCHANGED.sav").write_bytes(b"unchanged-player")
        (self.save_root / "Players/ABC_dps.sav").write_bytes(b"dps")
        (self.save_root / "LevelMeta.sav").write_bytes(b"meta")
        (self.save_root / "WorldOption.sav").write_bytes(b"options")
        result = replace_staged_files(
            save_root=self.save_root,
            staged_root=self.stage_root,
            transaction_root=self.transaction_root,
            relative_paths=self.paths,
            backup_enabled=True,
            verify=lambda: True,
            backup_paths=core_save_paths(self.save_root),
            backup_metadata={"StudioVersion": "test", "WorldId": "save"},
        )

        backup = Path(result.backup_path)
        self.assertEqual((backup / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((backup / "Players/ABC.sav").read_bytes(), b"old-player")
        self.assertEqual((backup / "Players/UNCHANGED.sav").read_bytes(), b"unchanged-player")
        self.assertEqual((backup / "Players/ABC_dps.sav").read_bytes(), b"dps")
        self.assertEqual((backup / "LevelMeta.sav").read_bytes(), b"meta")
        self.assertEqual((backup / "WorldOption.sav").read_bytes(), b"options")
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["StudioVersion"], "test")
        self.assertEqual(manifest["WorldId"], "save")
        self.assertEqual(set(manifest["Files"]), {
            "Level.sav",
            "LevelMeta.sav",
            "WorldOption.sav",
            "Players/ABC.sav",
            "Players/ABC_dps.sav",
            "Players/UNCHANGED.sav",
        })

    def test_backup_only_transaction_creates_verified_backup_without_writes(self) -> None:
        result = replace_staged_files(
            save_root=self.save_root,
            staged_root=self.stage_root,
            transaction_root=self.transaction_root,
            relative_paths=(),
            backup_enabled=True,
            verify=lambda: True,
            backup_paths=core_save_paths(self.save_root),
            files_skipped=self.paths,
            pre_write_check=lambda: True,
        )

        self.assertEqual(result.files_written, 0)
        self.assertEqual(result.files_changed, ())
        self.assertEqual(set(result.files_skipped), {"Level.sav", "Players/ABC.sav"})
        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((self.save_root / "Players/ABC.sav").read_bytes(), b"old-player")
        backup = Path(result.backup_path)
        self.assertEqual((backup / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((backup / "Players/ABC.sav").read_bytes(), b"old-player")

    def test_manifest_detects_any_core_file_change(self) -> None:
        (self.save_root / "Players/ABC_dps.sav").write_bytes(b"dps")
        manifest = capture_source_manifest(self.save_root)
        self.assertTrue(source_manifest_matches(self.save_root, manifest))
        (self.save_root / "Players/ABC_dps.sav").write_bytes(b"changed")
        self.assertFalse(source_manifest_matches(self.save_root, manifest))

    def test_pre_write_source_change_performs_zero_writes(self) -> None:
        with self.assertRaisesRegex(SaveTransactionError, "changed while the backup"):
            replace_staged_files(
                save_root=self.save_root,
                staged_root=self.stage_root,
                transaction_root=self.transaction_root,
                relative_paths=self.paths,
                backup_enabled=True,
                verify=lambda: True,
                pre_write_check=lambda: False,
            )
        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((self.save_root / "Players/ABC.sav").read_bytes(), b"old-player")

    def test_replacement_failure_restores_every_original(self) -> None:
        from palworld_save_studio.core import save_transaction

        real_replace = save_transaction.os.replace
        calls = 0

        def fail_second_replace(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated replacement failure")
            return real_replace(source, target)

        with patch.object(save_transaction.os, "replace", side_effect=fail_second_replace):
            with self.assertRaises(SaveTransactionError):
                replace_staged_files(
                    save_root=self.save_root,
                    staged_root=self.stage_root,
                    transaction_root=self.transaction_root,
                    relative_paths=self.paths,
                    backup_enabled=False,
                    verify=lambda: True,
                )

        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((self.save_root / "Players/ABC.sav").read_bytes(), b"old-player")

    def test_verification_failure_restores_every_original(self) -> None:
        with self.assertRaisesRegex(SaveTransactionError, "did not match"):
            replace_staged_files(
                save_root=self.save_root,
                staged_root=self.stage_root,
                transaction_root=self.transaction_root,
                relative_paths=self.paths,
                backup_enabled=False,
                verify=lambda: False,
            )

        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((self.save_root / "Players/ABC.sav").read_bytes(), b"old-player")

    def test_missing_staged_file_performs_zero_writes(self) -> None:
        (self.stage_root / "Level.sav").unlink()
        with self.assertRaisesRegex(SaveTransactionError, "Missing staged file"):
            replace_staged_files(
                save_root=self.save_root,
                staged_root=self.stage_root,
                transaction_root=self.transaction_root,
                relative_paths=self.paths,
                backup_enabled=False,
                verify=lambda: True,
            )
        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")

    def test_backup_failure_performs_zero_writes(self) -> None:
        with patch(
            "palworld_save_studio.core.save_transaction.create_persistent_backup",
            side_effect=OSError("simulated backup failure"),
        ):
            with self.assertRaisesRegex(SaveTransactionError, "Backup creation failed"):
                replace_staged_files(
                    save_root=self.save_root,
                    staged_root=self.stage_root,
                    transaction_root=self.transaction_root,
                    relative_paths=self.paths,
                    backup_enabled=True,
                    verify=lambda: True,
                )
        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")

    def test_backup_verification_failure_performs_zero_writes(self) -> None:
        fake_backup = self.root / "bad-backup"
        (fake_backup / "Players").mkdir(parents=True)
        (fake_backup / "Level.sav").write_bytes(b"wrong-level")
        (fake_backup / "Players/ABC.sav").write_bytes(b"old-player")
        with patch(
            "palworld_save_studio.core.save_transaction.create_persistent_backup",
            return_value=fake_backup,
        ):
            with self.assertRaisesRegex(SaveTransactionError, "Backup verification failed"):
                replace_staged_files(
                    save_root=self.save_root,
                    staged_root=self.stage_root,
                    transaction_root=self.transaction_root,
                    relative_paths=self.paths,
                    backup_enabled=True,
                    verify=lambda: True,
                )
        self.assertEqual((self.save_root / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((self.save_root / "Players/ABC.sav").read_bytes(), b"old-player")


if __name__ == "__main__":
    unittest.main()

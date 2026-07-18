import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from palworld_save_studio.core.save_transaction import (
    BACKUP_FOLDER_NAME,
    SaveTransactionError,
    replace_staged_files,
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
        result = replace_staged_files(
            save_root=self.save_root,
            staged_root=self.stage_root,
            transaction_root=self.transaction_root,
            relative_paths=self.paths,
            backup_enabled=True,
            verify=lambda: True,
        )

        backup = Path(result.backup_path)
        self.assertEqual((backup / "Level.sav").read_bytes(), b"old-level")
        self.assertEqual((backup / "Players/ABC.sav").read_bytes(), b"old-player")
        self.assertEqual((backup / "Players/UNCHANGED.sav").read_bytes(), b"unchanged-player")

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


if __name__ == "__main__":
    unittest.main()

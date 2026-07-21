import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from palworld_save_studio.core.save_manager import SaveManager
from palworld_save_studio.core.save_transaction import (
    SaveTransactionError,
    capture_source_manifest,
)


class DedicatedSaveModeTests(unittest.TestCase):
    def test_world_id_root_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = Path(temporary) / "WorldId"
            (world / "Players").mkdir(parents=True)
            (world / "Level.sav").write_bytes(b"fixture")
            SaveManager._validate_save_root(world, "dedicated")

    def test_parent_with_one_nested_world_is_rejected_with_exact_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary) / "0"
            world = parent / "WorldId"
            (world / "Players").mkdir(parents=True)
            (world / "Level.sav").write_bytes(b"fixture")
            with self.assertRaisesRegex(
                SaveTransactionError, "Select the WorldID folder directly"
            ) as raised:
                SaveManager._validate_save_root(parent, "dedicated")
            self.assertIn(str(world), str(raised.exception))

    def test_incomplete_world_id_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = Path(temporary) / "WorldId"
            world.mkdir()
            (world / "Level.sav").write_bytes(b"fixture")
            with self.assertRaisesRegex(SaveTransactionError, "directly contain"):
                SaveManager._validate_save_root(world, "dedicated")

    def test_archive_outer_folder_is_rejected_with_exact_world_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            outer = Path(temporary) / "archive"
            world = outer / "0" / "WorldId"
            (world / "Players").mkdir(parents=True)
            (world / "Level.sav").write_bytes(b"fixture")
            with self.assertRaisesRegex(
                SaveTransactionError, "Select the WorldID folder directly"
            ) as raised:
                SaveManager._validate_save_root(outer, "dedicated")
            self.assertIn(str(world), str(raised.exception))

    def test_dedicated_commit_requires_server_stop_confirmation_before_serializing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = Path(temporary) / "WorldId"
            (world / "Players").mkdir(parents=True)
            (world / "Level.sav").write_bytes(b"fixture")
            manager = SaveManager()
            state = manager._capture_runtime_state()
            try:
                manager._loaded = True
                manager._file_path = world
                manager._save_kind = "dedicated"
                manager._dirty_revision = 1
                manager._source_manifest = capture_source_manifest(world)
                manager._source_verified = True
                with patch.object(manager, "_serialize_to") as serialize:
                    with self.assertRaisesRegex(SaveTransactionError, "PalServer"):
                        manager.commit(server_stopped_confirmed=False)
                    serialize.assert_not_called()
            finally:
                manager._restore_runtime_state(state)

    def test_source_change_aborts_before_serializing_even_without_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = Path(temporary) / "WorldId"
            (world / "Players").mkdir(parents=True)
            level = world / "Level.sav"
            level.write_bytes(b"original")
            manager = SaveManager()
            state = manager._capture_runtime_state()
            try:
                manager._loaded = True
                manager._file_path = world
                manager._save_kind = "dedicated"
                manager._dirty_revision = 0
                manager._source_manifest = capture_source_manifest(world)
                manager._source_verified = True
                level.write_bytes(b"changed externally")
                with patch.object(manager, "_serialize_to") as serialize:
                    with self.assertRaisesRegex(SaveTransactionError, "changed on disk"):
                        manager.commit(server_stopped_confirmed=True)
                    serialize.assert_not_called()
            finally:
                manager._restore_runtime_state(state)

    def test_dedicated_skip_report_lists_every_unwritten_core_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = Path(temporary) / "WorldId"
            (world / "Players").mkdir(parents=True)
            (world / "Level.sav").write_bytes(b"level")
            (world / "LevelMeta.sav").write_bytes(b"meta")
            (world / "WorldOption.sav").write_bytes(b"option")
            (world / "Players/ABC.sav").write_bytes(b"player")
            (world / "Players/ABC_dps.sav").write_bytes(b"dps")
            manager = SaveManager()
            state = manager._capture_runtime_state()
            try:
                manager._file_path = world
                manager._save_kind = "dedicated"
                skipped = manager._reported_skipped_paths(
                    [Path("Level.sav")],
                    [Path("Players/ABC.sav")],
                )
                self.assertEqual(
                    set(skipped),
                    {
                        Path("LevelMeta.sav"),
                        Path("WorldOption.sav"),
                        Path("Players/ABC.sav"),
                        Path("Players/ABC_dps.sav"),
                    },
                )
            finally:
                manager._restore_runtime_state(state)


if __name__ == "__main__":
    unittest.main()

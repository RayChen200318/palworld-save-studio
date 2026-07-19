import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from palworld_save_studio.utils import util


class PathBrowserTests(unittest.TestCase):
    def test_non_windows_root_is_the_filesystem_root(self) -> None:
        if os.name == "nt":
            self.skipTest("Non-Windows behavior")
        self.assertEqual(util.get_path_roots(), [Path.cwd().anchor])

    def test_windows_roots_include_available_local_removable_and_mapped_drives(self) -> None:
        candidates = ["C:\\", "D:\\", "E:\\", "Z:\\"]
        available = {"C:\\", "D:\\", "Z:\\"}
        with (
            patch.object(util.os, "name", "nt"),
            patch.object(util, "_windows_drive_candidates", return_value=candidates),
            patch.object(util.os.path, "isdir", side_effect=lambda path: path in available),
        ):
            self.assertEqual(util.get_path_roots(), ["C:\\", "D:\\", "Z:\\"])

    def test_path_context_returns_roots_children_and_world_status(self) -> None:
        with TemporaryDirectory() as temp_directory:
            world_path = Path(temp_directory) / "World"
            players_path = world_path / "Players"
            child_path = world_path / "AnotherFolder"
            players_path.mkdir(parents=True)
            child_path.mkdir()
            (world_path / "Level.sav").write_bytes(b"fixture")

            with patch.object(util, "get_path_roots", return_value=["/"]):
                context = util.get_path_context(world_path)

        self.assertEqual(context["currentPath"], str(world_path.resolve()))
        self.assertEqual(context["roots"], ["/"])
        self.assertTrue(context["isPalDir"])
        self.assertTrue(context["children"][str(players_path.resolve())]["isDir"])
        self.assertFalse(
            context["children"][str((world_path / "Level.sav").resolve())]["isDir"]
        )

    def test_path_context_rejects_a_file(self) -> None:
        with TemporaryDirectory() as temp_directory:
            file_path = Path(temp_directory) / "Level.sav"
            file_path.write_bytes(b"fixture")
            with self.assertRaises(NotADirectoryError):
                util.get_path_context(file_path)


if __name__ == "__main__":
    unittest.main()

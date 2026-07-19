import unittest
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token

from palworld_save_studio.config import Config
from palworld_save_studio.core.item_inventory import ItemInventoryError
from palworld_save_studio.webui import app


class SaveApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True)
        with app.app_context():
            self.token = create_access_token(identity="test", expires_delta=False)
        self.client = app.test_client()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.original_backup_enabled = Config.backup_enabled
        self.original_path = Config.path

    def tearDown(self) -> None:
        Config.backup_enabled = self.original_backup_enabled
        Config.path = self.original_path

    def test_path_browser_opens_an_absolute_world_directory(self) -> None:
        with TemporaryDirectory() as temp_directory:
            world_path = Path(temp_directory) / "World"
            (world_path / "Players").mkdir(parents=True)
            (world_path / "Level.sav").write_bytes(b"fixture")

            with patch.object(Config, "save_to_file") as save_config:
                response = self.client.post(
                    "/api/save/path",
                    headers=self.headers,
                    json={"path": str(world_path)},
                )

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], 0)
        self.assertEqual(payload["data"]["currentPath"], str(world_path.resolve()))
        self.assertTrue(payload["data"]["isPalDir"])
        self.assertTrue(payload["data"]["roots"])
        self.assertEqual(Config.path, str(world_path.resolve()))
        save_config.assert_not_called()

    def test_path_browser_rejects_invalid_paths_without_changing_state(self) -> None:
        Config.path = "/last/successful/path"
        with TemporaryDirectory() as temp_directory:
            file_path = Path(temp_directory) / "Level.sav"
            file_path.write_bytes(b"fixture")
            cases = (
                (None, 400),
                ("", 400),
                ("~", 400),
                ("relative/path", 400),
                (str(file_path), 400),
                (str(Path(temp_directory) / "missing"), 404),
            )
            for raw_path, expected_status in cases:
                with self.subTest(path=raw_path):
                    response = self.client.post(
                        "/api/save/path",
                        headers=self.headers,
                        json={"path": raw_path},
                    )
                    self.assertEqual(response.status_code, expected_status)
                    self.assertEqual(response.get_json()["status"], 1)
                    self.assertEqual(Config.path, "/last/successful/path")

    def test_path_browser_maps_permission_and_network_errors_atomically(self) -> None:
        Config.path = "/last/successful/path"
        inaccessible_path = str(Path.cwd().resolve())
        network_error = OSError("network share unavailable")
        network_error.winerror = 67

        for error, expected_status in (
            (PermissionError("denied"), 403),
            (network_error, 404),
            (OSError("unclassified"), 500),
        ):
            with self.subTest(error=error):
                with patch(
                    "palworld_save_studio.api.save.get_path_context",
                    side_effect=error,
                ):
                    response = self.client.post(
                        "/api/save/path",
                        headers=self.headers,
                        json={"path": inaccessible_path},
                    )
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(Config.path, "/last/successful/path")

    @unittest.skipUnless(os.name == "nt", "Windows path syntax is tested on Windows CI")
    def test_path_browser_accepts_drive_and_unc_absolute_paths_on_windows(self) -> None:
        Config.path = r"C:\last"
        contexts = {
            r"D:\Palworld\World": {
                "currentPath": r"D:\Palworld\World",
                "roots": ["C:\\", "D:\\"],
                "children": {},
                "isPalDir": True,
            },
            r"\\server\share\World": {
                "currentPath": r"\\server\share\World",
                "roots": ["C:\\", "D:\\"],
                "children": {},
                "isPalDir": True,
            },
        }

        def context_for(path: Path):
            return contexts[str(path)]

        with patch(
            "palworld_save_studio.api.save.get_path_context",
            side_effect=context_for,
        ):
            for raw_path in contexts:
                with self.subTest(path=raw_path):
                    response = self.client.post(
                        "/api/save/path",
                        headers=self.headers,
                        json={"path": raw_path},
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        response.get_json()["data"]["currentPath"], raw_path
                    )
                    self.assertEqual(Config.path, raw_path)

    @unittest.skipUnless(os.name == "nt", "Cross-drive integration runs on Windows CI")
    def test_path_browser_navigates_to_a_real_d_drive_world_on_windows(self) -> None:
        mapped_drive = False
        backing_directory = None
        drive_test_directory = None
        drive_root = Path("D:\\")
        if not drive_root.exists():
            backing_directory = TemporaryDirectory()
            subprocess.run(
                ["subst", "D:", backing_directory.name],
                check=True,
                capture_output=True,
            )
            mapped_drive = True

        try:
            try:
                drive_test_directory = TemporaryDirectory(dir=drive_root)
            except OSError as exc:
                self.skipTest(f"D: is not writable on this Windows runner: {exc}")
            world_path = Path(drive_test_directory.name) / "World"
            (world_path / "Players").mkdir(parents=True, exist_ok=True)
            (world_path / "Level.sav").write_bytes(b"fixture")
            Config.path = r"C:\last"

            response = self.client.post(
                "/api/save/path",
                headers=self.headers,
                json={"path": str(world_path)},
            )

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()["data"]
            self.assertEqual(payload["currentPath"], str(world_path.resolve()))
            self.assertIn("D:\\", payload["roots"])
            self.assertTrue(payload["isPalDir"])
        finally:
            if drive_test_directory is not None:
                drive_test_directory.cleanup()
            if mapped_drive:
                subprocess.run(
                    ["subst", "D:", "/D"],
                    check=True,
                    capture_output=True,
                )
                backing_directory.cleanup()

    def test_session_uses_existing_response_envelope(self) -> None:
        manager = MagicMock()
        manager.session_summary.return_value = {
            "Path": "C:/Save",
            "Loaded": True,
            "DirtyRevision": 3,
            "Dirty": True,
            "Statistics": {"Players": 1, "Pals": 2, "Humans": 1, "Anomalies": 0, "Objects": 3},
            "BackupEnabled": True,
            "BackupPath": "C:/Save/Palworld-Save-Studio-Backup",
            "LastCommit": None,
        }
        with patch("palworld_save_studio.api.save.SaveManager", return_value=manager):
            response = self.client.get("/api/save/session", headers=self.headers)
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], 0)
        self.assertEqual(payload["data"]["DirtyRevision"], 3)

    def test_commit_writes_only_the_loaded_session(self) -> None:
        manager = MagicMock()
        manager.commit.return_value = {"Verified": True, "FilesWritten": 2, "BackupPath": None, "Revision": 0}
        manager.session_summary.return_value = {"Path": "C:/Save", "Loaded": True, "DirtyRevision": 0, "Dirty": False}
        with patch("palworld_save_studio.api.save.SaveManager", return_value=manager):
            response = self.client.post(
                "/api/save/commit",
                headers=self.headers,
                json={"WritePath": "C:/Different-Save"},
            )
        self.assertEqual(response.status_code, 200)
        manager.commit.assert_called_once_with()

    def test_load_refuses_to_replace_an_existing_draft(self) -> None:
        manager = MagicMock()
        manager.has_draft = True
        with patch("palworld_save_studio.api.save.SaveManager", return_value=manager):
            response = self.client.post(
                "/api/save/load",
                headers=self.headers,
                json={"ReadPath": "C:/Different-Save"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("Discard", response.get_json()["msg"])
        manager.open.assert_not_called()

    def test_backup_setting_requires_a_boolean(self) -> None:
        response = self.client.patch(
            "/api/save/settings",
            headers=self.headers,
            json={"BackupEnabled": "no"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], 1)

    def test_update_check_route_is_not_registered(self) -> None:
        routes = {rule.rule for rule in app.url_map.iter_rules()}
        self.assertNotIn("/api/save/update", routes)

    def test_technology_catalog_uses_string_labels(self) -> None:
        response = self.client.get("/api/save/tech_data", headers=self.headers)
        groups = response.get_json()["data"]["techLvDict"]
        first_item = next(item for items in groups.values() for item in items)
        self.assertIsInstance(first_item["I18n"], str)

    def test_pal_and_skill_catalogs_include_both_supported_languages(self) -> None:
        pal = self.client.get("/api/save/pal_data", headers=self.headers).get_json()[
            "data"
        ]["dict"]["Anubis"]
        passive = self.client.get(
            "/api/save/passive_skills", headers=self.headers
        ).get_json()["data"]["dict"]["Legend"]
        active_payload = self.client.get(
            "/api/save/active_skills", headers=self.headers
        ).get_json()["data"]["arr"]
        active = next(item for item in active_payload if item["I18n"]["en"]["Description"])
        active_without_description = next(
            item for item in active_payload if not item["I18n"]["en"]["Description"]
        )

        self.assertEqual(set(pal["I18n"]), {"en", "zh-CN"})
        self.assertEqual(set(passive["I18n"]), {"en", "zh-CN"})
        self.assertTrue(passive["I18n"]["zh-CN"]["Description"])
        self.assertEqual(set(active["I18n"]), {"en", "zh-CN"})
        self.assertTrue(active["I18n"]["en"]["Description"])
        self.assertEqual(
            active_without_description["I18n"]["en"]["Description"], ""
        )
        self.assertTrue(active_without_description["I18n"]["en"]["Name"])

    def test_verified_mutation_passives_are_flagged_exclusively(self) -> None:
        payload = self.client.get(
            "/api/save/passive_skills", headers=self.headers
        ).get_json()["data"]["dict"]
        expected = {
            "MutationPal_Babysitter",
            "MutationPal_Mutant",
            "MutationPal_Immortal",
            "MutationPal_ExplosionResist",
        }
        actual = {
            key for key, value in payload.items() if value["IsMutationExclusive"]
        }
        self.assertEqual(actual, expected)

    def test_item_mutation_marks_one_dirty_revision(self) -> None:
        manager = MagicMock()
        manager._loaded = True
        manager.item_inventory.add_item.return_value = {"PlayerId": "player-1", "Containers": {}}
        manager.mark_dirty.return_value = 4
        with patch("palworld_save_studio.api.item.SaveManager", return_value=manager):
            response = self.client.post(
                "/api/item/player/player-1",
                headers=self.headers,
                json={"StaticId": "Wood", "Container": "common", "Quantity": 20, "SlotIndex": 2},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["DirtyRevision"], 4)
        manager.item_inventory.add_item.assert_called_once_with(
            "player-1", "Wood", "common", 20, 2, None
        )
        manager.mark_dirty.assert_called_once_with()

    def test_rejected_item_mutation_does_not_mark_dirty(self) -> None:
        manager = MagicMock()
        manager._loaded = True
        manager.item_inventory.move_item.side_effect = ItemInventoryError("incompatible target")
        with patch("palworld_save_studio.api.item.SaveManager", return_value=manager):
            response = self.client.post(
                "/api/item/player/player-1/move",
                headers=self.headers,
                json={
                    "Source": {"Container": "common", "SlotIndex": 0},
                    "Target": {"Container": "armor", "SlotIndex": 0},
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("incompatible", response.get_json()["msg"])
        manager.mark_dirty.assert_not_called()

    def test_rejected_pal_gear_stack_does_not_mark_dirty(self) -> None:
        manager = MagicMock()
        manager._loaded = True
        manager.item_inventory.add_item.side_effect = ItemInventoryError(
            "Pal Gear quantity must be exactly 1."
        )
        with patch("palworld_save_studio.api.item.SaveManager", return_value=manager):
            response = self.client.post(
                "/api/item/player/player-1",
                headers=self.headers,
                json={
                    "StaticId": "SkillUnlock_IceHorse",
                    "Container": "essential",
                    "Quantity": 2,
                    "SlotIndex": 10,
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("exactly 1", response.get_json()["msg"])
        manager.mark_dirty.assert_not_called()

    def test_dangerous_item_delete_forwards_explicit_confirmation(self) -> None:
        manager = MagicMock()
        manager._loaded = True
        manager.item_inventory.delete_item.return_value = {"PlayerId": "player-1", "Containers": {}}
        manager.mark_dirty.return_value = 5
        with patch("palworld_save_studio.api.item.SaveManager", return_value=manager):
            response = self.client.delete(
                "/api/item/player/player-1/essential/0",
                headers=self.headers,
                json={"ConfirmDangerous": True},
            )

        self.assertEqual(response.status_code, 200)
        manager.item_inventory.delete_item.assert_called_once_with(
            "player-1", "essential", 0, True
        )


if __name__ == "__main__":
    unittest.main()

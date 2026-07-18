import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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

    def tearDown(self) -> None:
        Config.backup_enabled = self.original_backup_enabled

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

    def test_update_check_reads_the_new_repository_release_status(self) -> None:
        result = {
            "CurrentVersion": "0.2.0-beta.1",
            "LatestVersion": None,
            "UpdateAvailable": False,
            "ReleaseUrl": None,
        }
        with patch(
            "palworld_save_studio.api.save.get_release_status",
            new=AsyncMock(return_value=result),
        ):
            response = self.client.get("/api/save/update", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"], result)

    def test_technology_catalog_uses_string_labels(self) -> None:
        response = self.client.get("/api/save/tech_data", headers=self.headers)
        groups = response.get_json()["data"]["techLvDict"]
        first_item = next(item for items in groups.values() for item in items)
        self.assertIsInstance(first_item["I18n"], str)

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

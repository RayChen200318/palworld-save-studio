import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from palworld_save_studio.core.save_manager import SaveManager


class SaveManagerCollectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = SaveManager()
        self.state = self.manager._capture_runtime_state()

    def tearDown(self) -> None:
        self.manager._restore_runtime_state(self.state)

    def test_global_collection_deduplicates_instances(self) -> None:
        pal = SimpleNamespace(
            InstanceId="pal-1",
            ContainerId="palbox-1",
            LastOwnerPlayerUId=None,
            OwnerPlayerUId="player-1",
        )
        player = SimpleNamespace(
            PlayerUId="player-1",
            OtomoCharacterContainerId="party-1",
            PalStorageContainerId="palbox-1",
            _palbox={"pal-1": pal},
        )
        self.manager.player_mapping = {"player-1": player}
        self.manager.baseworker_mapping = {"pal-1": pal}
        self.manager._dangling_pals = {"pal-1": pal}

        contexts = self.manager.get_all_pal_contexts()

        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["location"], "base")

    def test_new_objects_target_only_the_players_palbox(self) -> None:
        player = SimpleNamespace(
            PlayerUId="player-1",
            OtomoCharacterContainerId="party-1",
            PalStorageContainerId="palbox-1",
            group_id="group-1",
        )
        full_palbox = MagicMock()
        full_palbox.get_empty_slot.return_value = -1
        self.manager.container_data = MagicMock()
        self.manager.container_data.get_container.return_value = full_palbox

        with patch.object(SaveManager, "get_player", return_value=player):
            result = self.manager.add_pal("player-1", character_id="WorldTreeDragon")

        self.assertIsNone(result)
        self.manager.container_data.get_container.assert_called_once_with("palbox-1")

    def test_delete_removes_every_reference_to_the_instance(self) -> None:
        raw = {"pal": "raw"}
        pal = SimpleNamespace(
            InstanceId="pal-1",
            group_id="group-1",
            ContainerId="container-1",
            _pal_obj=raw,
        )
        player = MagicMock()
        player.get_pal.return_value = pal
        self.manager.player_mapping = {"player-1": player}
        self.manager.baseworker_mapping = {"pal-1": pal}
        self.manager._dangling_pals = {"pal-1": pal}
        self.manager._entities_list = [raw]
        group = MagicMock()
        container = MagicMock()
        self.manager.group_data = MagicMock()
        self.manager.group_data.get_group.return_value = group
        self.manager.group_data.get_groups.return_value = [group]
        self.manager.container_data = MagicMock()
        self.manager.container_data.get_container.return_value = container

        self.assertTrue(self.manager.delete_pal("pal-1"))
        self.assertNotIn("pal-1", self.manager.baseworker_mapping)
        self.assertNotIn("pal-1", self.manager._dangling_pals)
        self.assertEqual(self.manager._entities_list, [])
        player.pop_pal.assert_called_once_with("pal-1")
        group.del_pal.assert_called_once_with("pal-1")
        container.del_pal.assert_called_once_with("pal-1")


if __name__ == "__main__":
    unittest.main()

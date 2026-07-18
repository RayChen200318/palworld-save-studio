import unittest

from palworld_save_studio.core.group_data import GroupData, PalGroup


class StringableId:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return self.value


class GroupDataIdentifierTests(unittest.TestCase):
    def test_group_lookup_normalizes_uuid_like_identifiers(self) -> None:
        group_data = GroupData.__new__(GroupData)
        expected = object()
        group_data.group_map = {"group-1": expected}

        self.assertIs(group_data.get_group(StringableId("group-1")), expected)

    def test_pal_and_player_membership_normalize_identifiers(self) -> None:
        group = PalGroup.__new__(PalGroup)
        handle = {"instance_id": "pal-1"}
        group.instance_map = {"pal-1": handle}
        group.player_map = {"player-1": object()}
        group._group_param = {
            "individual_character_handle_ids": [handle],
            "guild_name": "Test Guild",
        }

        self.assertTrue(group.has_pal(StringableId("pal-1")))
        self.assertTrue(group.has_player(StringableId("player-1")))
        group.del_pal(StringableId("pal-1"))
        self.assertFalse(group.has_pal("pal-1"))
        self.assertEqual(group.individual_character_handle_ids, [])


if __name__ == "__main__":
    unittest.main()

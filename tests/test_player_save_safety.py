import copy
from types import SimpleNamespace
import unittest

from palworld_save_studio.api.pal import _atomic_pal
from palworld_save_studio.api.player import _atomic_player, _validated_player_changes
from palworld_save_studio.core.pal_objects import PalObjects
from palworld_save_studio.core.player_entity import PlayerEntity
from palworld_save_studio.core.save_schema import SaveSchemaError, validate_player_schema


class PlayerSaveSafetyTests(unittest.TestCase):
    @staticmethod
    def player() -> PlayerEntity:
        player = object.__new__(PlayerEntity)
        player._player_key = {
            "PlayerUId": {"value": "player-1"},
            "InstanceId": {"value": "instance-1"},
        }
        player._player_param = {
            "IsPlayer": PalObjects.BoolProperty(True),
            "Level": PalObjects.ByteProperty(50),
            "Exp": PalObjects.Int64Property(100),
        }
        player._player_save_data = {
            "IndividualId": {
                "value": {
                    "PlayerUId": {"value": "player-1"},
                    "InstanceId": {"value": "instance-1"},
                }
            }
        }
        player._palbox = {}
        player._new_palbox = {}
        return player

    def test_missing_unused_status_points_are_created_as_uint16(self) -> None:
        player = self.player()
        player.Level = 80
        self.assertEqual(player.UnusedStatusPoint, 30)
        self.assertEqual(
            player._player_param["UnusedStatusPoint"]["type"], "UInt16Property"
        )
        validate_player_schema(player)

    def test_uint16_constructor_rejects_invalid_values(self) -> None:
        for value in (-1, 65536, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                PalObjects.UInt16Property(value)

    def test_wrong_unused_status_point_type_is_rejected(self) -> None:
        player = self.player()
        player._player_param["UnusedStatusPoint"] = PalObjects.IntProperty(30)
        with self.assertRaisesRegex(SaveSchemaError, "UInt16Property"):
            validate_player_schema(player)

    def test_present_but_null_property_is_rejected_as_invalid_structure(self) -> None:
        player = self.player()
        player._player_param["UnusedStatusPoint"] = None
        with self.assertRaisesRegex(SaveSchemaError, "UInt16Property"):
            validate_player_schema(player)

    def test_out_of_range_progression_is_rejected_independently(self) -> None:
        player = self.player()
        player._player_param["Level"] = PalObjects.ByteProperty(81)
        with self.assertRaisesRegex(SaveSchemaError, "Player.*Level"):
            validate_player_schema(player)

    def test_status_point_reads_do_not_create_missing_fields(self) -> None:
        player = self.player()
        before = copy.deepcopy(player._player_param)
        self.assertIsNone(player.StatusPointHP)
        self.assertIsNone(player.StatusPointSP)
        self.assertIsNone(player.ExStatusPointATK)
        self.assertEqual(player._player_param, before)

    def test_full_player_request_is_validated_before_any_field_changes(self) -> None:
        player = self.player()
        before = copy.deepcopy(player._player_param)
        with self.assertRaisesRegex(ValueError, "between 1"):
            _validated_player_changes(
                player,
                {"NickName": "would-have-been-applied", "Level": 999},
            )
        self.assertEqual(player._player_param, before)

    def test_player_runtime_failure_restores_both_save_objects(self) -> None:
        player = self.player()
        parameter_before = copy.deepcopy(player._player_param)
        save_data_before = copy.deepcopy(player._player_save_data)
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            with _atomic_player(player):
                player._player_param["NickName"] = PalObjects.StrProperty("changed")
                player._player_save_data["TechnologyPoint"] = PalObjects.IntProperty(99)
                raise RuntimeError("simulated setter failure")
        self.assertEqual(player._player_param, parameter_before)
        self.assertEqual(player._player_save_data, save_data_before)

    def test_pal_runtime_failure_restores_the_complete_parameter_map(self) -> None:
        pal = SimpleNamespace(
            _pal_param={
                "Level": PalObjects.ByteProperty(50),
                "Exp": PalObjects.Int64Property(100),
            }
        )
        before = copy.deepcopy(pal._pal_param)
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            with _atomic_pal(pal):
                pal._pal_param["Level"]["value"] = 80
                pal._pal_param["Exp"]["value"] = 999
                raise RuntimeError("simulated setter failure")
        self.assertEqual(pal._pal_param, before)


if __name__ == "__main__":
    unittest.main()

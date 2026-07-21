import unittest
from pathlib import Path
from types import SimpleNamespace

from palworld_save_tools.archive import UUID

from palworld_save_studio.core.item_inventory import (
    CONTAINER_PROPERTIES,
    ItemInventoryError,
    ItemInventoryService,
    ZERO_UUID,
)
from palworld_save_studio.utils.data_provider import DataProvider


def _uuid(index: int) -> UUID:
    return UUID.from_str(f"00000000-0000-0000-0000-{index:012d}")


class FakeManager:
    def __init__(self) -> None:
        inventory = {}
        container_entries = []
        capacities = {
            "common": 54,
            "essential": 230,
            "food": 5,
            "weapon": 6,
            "armor": 9,
            "drop": 4,
        }
        for index, (name, property_name) in enumerate(CONTAINER_PROPERTIES.items(), 10):
            container_id = _uuid(index)
            inventory[property_name] = {"value": {"ID": {"value": container_id}}}
            container_entries.append(
                {
                    "key": {"ID": {"value": container_id}},
                    "value": {
                        "SlotNum": {"value": capacities[name]},
                        "Slots": {"value": {"values": []}},
                    },
                }
            )
        self.player = SimpleNamespace(
            PlayerUId="player-1",
            NickName="Tester",
            _player_save_data={"InventoryInfo": {"value": inventory}},
        )
        world = {
            "ItemContainerSaveData": {"value": container_entries},
            "DynamicItemSaveData": {"value": {"values": []}},
        }
        self.gvas_file = SimpleNamespace(properties={"worldSaveData": {"value": world}})

    def get_player(self, player_id: str):
        return self.player if player_id == "player-1" else None


class ItemCatalogTests(unittest.TestCase):
    def test_catalog_is_legal_bilingual_and_explicitly_grouped(self) -> None:
        data = DataProvider.get_item_catalog()
        self.assertGreater(len(data["Items"]), 2000)
        self.assertGreater(len(data["Groups"]), 1500)
        self.assertFalse(any(key.startswith("BossDefeatReward_") for key in data["Items"]))
        for static_id, item in data["Items"].items():
            self.assertEqual(item["StaticId"], static_id)
            self.assertTrue(item["I18n"]["en"])
            self.assertTrue(item["I18n"]["zh-CN"])
            self.assertGreaterEqual(item["MaxStack"], 1)
            self.assertTrue(item["AllowedContainers"])
        for group in data["Groups"]:
            self.assertTrue(group["Variants"])
            self.assertTrue(all(value in data["Items"] for value in group["Variants"]))
        grouped_variants = {
            static_id for group in data["Groups"] for static_id in group["Variants"]
        }
        self.assertEqual(grouped_variants, set(data["Items"]))
        self.assertEqual(
            data["Source"]["PalworldSavePalCommit"],
            "0d99b04acba369ec88550d122794b9917bbf820e",
        )

    def test_every_catalog_icon_is_a_nonempty_webp(self) -> None:
        data = DataProvider.get_item_catalog()
        icon_root = (
            Path(__file__).resolve().parents[1]
            / "src/palworld_save_studio/assets/icons/items"
        )
        missing = []
        invalid = []
        for icon_key in {item["IconKey"] for item in data["Items"].values()}:
            path = icon_root / f"{icon_key}.webp"
            if not path.is_file():
                missing.append(icon_key)
            elif not (path.read_bytes()[:4] == b"RIFF" and path.read_bytes()[8:12] == b"WEBP"):
                invalid.append(icon_key)
        self.assertEqual(missing, [])
        self.assertEqual(invalid, [])

    def test_formal_rarity_variants_are_frozen_in_the_catalog(self) -> None:
        variants = DataProvider.get_item_variants("HandGun_Default")
        self.assertEqual(
            [item["StaticId"] for item in variants],
            [f"HandGun_Default{suffix}" for suffix in ("", "_2", "_3", "_4", "_5")],
        )

    def test_every_pal_gear_item_has_a_single_item_stack(self) -> None:
        data = DataProvider.get_item_catalog()
        pal_gear = [
            item for item in data["Items"].values()
            if item.get("TypeB") == "Essential_PalGear"
        ]
        self.assertGreater(len(pal_gear), 100)
        self.assertTrue(all(item["MaxStack"] == 1 for item in pal_gear))
        self.assertEqual(data["Items"]["SkillUnlock_IceHorse"]["MaxStack"], 1)

    def test_case_aliases_resolve_without_changing_the_canonical_catalog(self) -> None:
        expected = {
            "GunPowder2": "Gunpowder2",
            "SkillCard_StoneShotGun": "SkillCard_StoneShotgun",
            "bone": "Bone",
        }
        for raw_id, canonical in expected.items():
            with self.subTest(raw_id=raw_id):
                self.assertEqual(
                    DataProvider.get_item_data(raw_id)["StaticId"], canonical
                )
                self.assertEqual(DataProvider.resolve_item_static_id(raw_id), canonical)

    def test_gunpowder_group_has_correct_search_terms_and_icon(self) -> None:
        group = next(
            group
            for group in DataProvider.get_item_groups()
            if "Gunpowder2" in group["Variants"]
        )
        self.assertIn("火药", group["SearchTerms"])
        self.assertEqual(group["I18n"]["zh-CN"], "火药")
        self.assertEqual(group["IconKey"], "t_itemicon_material_gunpowder2")
        self.assertEqual(group["ManagedKind"], "normal")


class ItemInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ItemInventoryService(FakeManager())
        self.player = self.service._player("player-1")

    def _append(self, container: str, slot: int, static_id: str, count: int = 1) -> None:
        target = self.service._container(self.player, container)
        self.service._slot_values(target).append(
            self.service._new_slot(slot, static_id, count, ZERO_UUID)
        )
        self.service._reindex()

    def test_stack_move_partially_merges_and_preserves_remainder(self) -> None:
        self.service.add_item("player-1", "Wood", "common", 9000, 0)
        self.service.add_item("player-1", "Wood", "common", 2000, 1)

        result = self.service.move_item("player-1", "common", 1, "common", 0)
        slots = result["Containers"]["common"]["Slots"]

        self.assertEqual(slots[0]["Item"]["Quantity"], 9999)
        self.assertEqual(slots[1]["Item"]["Quantity"], 1001)

    def test_pal_gear_requires_quantity_one_but_allows_duplicate_slots(self) -> None:
        with self.assertRaisesRegex(ItemInventoryError, "exactly 1"):
            self.service.add_item(
                "player-1", "SkillUnlock_IceHorse", "essential", 2, 0
            )
        self.assertEqual(
            self.service.player_inventory("player-1")["Containers"]["essential"]["Slots"][0]["Item"],
            None,
        )

        self.service.add_item(
            "player-1", "SkillUnlock_IceHorse", "essential", 1, 0
        )
        result = self.service.add_item(
            "player-1", "SkillUnlock_IceHorse", "essential", 1, 1
        )
        self.assertEqual(result["Containers"]["essential"]["Slots"][0]["Item"]["Quantity"], 1)
        self.assertEqual(result["Containers"]["essential"]["Slots"][1]["Item"]["Quantity"], 1)

    def test_invalid_existing_pal_gear_quantity_is_flagged_and_repairable(self) -> None:
        self._append("essential", 0, "SkillUnlock_IceHorse", 3)
        item = self.service.player_inventory("player-1")["Containers"]["essential"]["Slots"][0]["Item"]
        self.assertIn("invalid-quantity", item["StateFlags"])

        with self.assertRaisesRegex(ItemInventoryError, "exactly 1"):
            self.service.patch_item("player-1", "essential", 0, {"Quantity": 2})
        result = self.service.patch_item(
            "player-1", "essential", 0, {"Quantity": 1}
        )
        repaired = result["Containers"]["essential"]["Slots"][0]["Item"]
        self.assertEqual(repaired["Quantity"], 1)
        self.assertNotIn("invalid-quantity", repaired["StateFlags"])

    def test_incompatible_move_is_atomic(self) -> None:
        self.service.add_item("player-1", "Wood", "common", 10, 0)
        before = self.service.semantic_snapshot()

        with self.assertRaisesRegex(ItemInventoryError, "incompatible"):
            self.service.move_item("player-1", "common", 0, "armor", 0)

        self.assertEqual(self.service.semantic_snapshot(), before)

    def test_compatible_equipment_swap_moves_both_dynamic_items_atomically(self) -> None:
        self.service.add_item("player-1", "HandGun_Default", "common", 1, 0)
        self.service.add_item("player-1", "MakeshiftHandgun", "weapon", 1, 0)

        result = self.service.move_item("player-1", "common", 0, "weapon", 0)

        self.assertEqual(result["Containers"]["weapon"]["Slots"][0]["Item"]["StaticId"], "HandGun_Default")
        self.assertEqual(result["Containers"]["common"]["Slots"][0]["Item"]["StaticId"], "MakeshiftHandgun")

    def test_dynamic_weapon_is_unique_and_rarity_preserves_durability_ratio(self) -> None:
        self.service.add_item("player-1", "HandGun_Default", "weapon", 1, 0)
        self.service.patch_item("player-1", "weapon", 0, {"Durability": 200})
        self.service.patch_item("player-1", "weapon", 0, {"StaticId": "HandGun_Default_5"})
        result = self.service.patch_item("player-1", "weapon", 0, {"Ammo": 16})
        item = result["Containers"]["weapon"]["Slots"][0]["Item"]
        dynamic_id = item["DynamicId"]
        self.assertEqual(item["Durability"], 1200)
        self.assertEqual(len(self.service.dynamic_references[dynamic_id]), 1)

        result = self.service.patch_item(
            "player-1", "weapon", 0, {"StaticId": "HandGun_Default"}
        )
        item = result["Containers"]["weapon"]["Slots"][0]["Item"]
        self.assertEqual(item["Durability"], 200)
        self.assertEqual(item["Ammo"], 8)
        self.assertEqual(item["PassiveSkills"], [])

    def test_egg_requires_a_legal_non_human_species(self) -> None:
        with self.assertRaisesRegex(ItemInventoryError, "EggCharacterId"):
            self.service.add_item("player-1", "PalEgg_Normal_01", "common", 1, 0)

        result = self.service.add_item(
            "player-1", "PalEgg_Normal_01", "common", 1, 0, "SheepBall"
        )
        self.assertEqual(
            result["Containers"]["common"]["Slots"][0]["Item"]["EggCharacterId"],
            "SheepBall",
        )

    def test_unknown_item_can_reorder_in_original_container_but_only_decrease(self) -> None:
        self._append("essential", 5, "Modded_Item", 7)
        self.service.move_item("player-1", "essential", 5, "essential", 6)
        with self.assertRaisesRegex(ItemInventoryError, "only be reduced"):
            self.service.patch_item("player-1", "essential", 6, {"Quantity": 8})
        result = self.service.patch_item("player-1", "essential", 6, {"Quantity": 4})
        self.assertEqual(result["Containers"]["essential"]["Slots"][6]["Item"]["Quantity"], 4)

    def test_drop_slot_is_recovery_only(self) -> None:
        self._append("drop", 0, "Wood", 5)
        with self.assertRaisesRegex(ItemInventoryError, "common inventory"):
            self.service.move_item("player-1", "drop", 0, "essential", 0)
        result = self.service.move_item("player-1", "drop", 0, "common", 0)
        self.assertEqual(result["Containers"]["common"]["Slots"][0]["Item"]["StaticId"], "Wood")

    def test_key_item_delete_requires_explicit_confirmation(self) -> None:
        self.service.add_item("player-1", "AdditionalInventory_001", "essential", 1, 0)
        before = self.service.semantic_snapshot()
        with self.assertRaisesRegex(ItemInventoryError, "explicit confirmation"):
            self.service.delete_item("player-1", "essential", 0)
        self.assertEqual(self.service.semantic_snapshot(), before)
        result = self.service.delete_item("player-1", "essential", 0, True)
        self.assertIsNone(result["Containers"]["essential"]["Slots"][0]["Item"])

    def test_capacity_item_delete_reorganizes_newly_locked_slots(self) -> None:
        self.service.add_item("player-1", "AdditionalInventory_001", "essential", 1, 0)
        self.service.add_item("player-1", "Wood", "common", 12, 44)

        result = self.service.delete_item("player-1", "essential", 0, True)
        common = result["Containers"]["common"]

        self.assertEqual(common["Capacity"], 42)
        self.assertEqual(common["Slots"][0]["Item"]["StaticId"], "Wood")
        self.assertIsNone(common["Slots"][44]["Item"])

    def test_capacity_item_delete_is_atomic_when_reorganization_has_no_space(self) -> None:
        self.service.add_item("player-1", "AdditionalInventory_001", "essential", 1, 0)
        for index in range(42):
            self._append("common", index, f"Modded_Full_{index}")
        self._append("common", 44, "Modded_Locked_Item")
        before = self.service.semantic_snapshot()

        with self.assertRaisesRegex(ItemInventoryError, "no legal space"):
            self.service.delete_item("player-1", "essential", 0, True)

        self.assertEqual(self.service.semantic_snapshot(), before)

    def test_invalid_dynamic_reference_blocks_related_mutation(self) -> None:
        self.service.add_item("player-1", "HandGun_Default", "weapon", 1, 0)
        weapon = self.service._slots_by_index(self.service._container(self.player, "weapon"))[0]
        clone = self.service._new_slot(1, "HandGun_Default", 1, ZERO_UUID)
        clone_raw = self.service._slot_raw(clone)
        clone_raw["item"]["dynamic_id"] = self.service._slot_raw(weapon)["item"]["dynamic_id"]
        self.service._slot_values(self.service._container(self.player, "weapon")).append(clone)
        self.service._reindex()

        before = self.service.semantic_snapshot()
        with self.assertRaisesRegex(ItemInventoryError, "multiple slot references"):
            self.service.delete_item("player-1", "weapon", 0)
        self.assertEqual(self.service.semantic_snapshot(), before)

    def test_delete_removes_only_the_now_unreferenced_dynamic_record(self) -> None:
        self.service.add_item("player-1", "HandGun_Default", "weapon", 1, 0)
        self.service.add_item("player-1", "ClothArmor", "armor", 1, 1)
        self.assertEqual(len(self.service.dynamic_entries), 2)

        self.service.delete_item("player-1", "weapon", 0)

        self.assertEqual(len(self.service.dynamic_entries), 1)
        remaining = self.service.dynamic_entries[0]["RawData"]["value"]["id"]["static_id"]
        self.assertEqual(remaining, "ClothArmor")

    def test_existing_case_aliases_keep_their_original_static_id(self) -> None:
        aliases = ("GunPowder2", "SkillCard_StoneShotGun", "bone")
        for index, static_id in enumerate(aliases):
            self._append("common", index, static_id)
        slots = self.service.player_inventory("player-1")["Containers"]["common"]["Slots"]
        self.assertEqual(
            [slots[index]["Item"]["StaticId"] for index in range(len(aliases))],
            list(aliases),
        )
        self.assertTrue(all(slots[index]["Item"]["IconKey"] for index in range(len(aliases))))

    def test_system_progress_record_is_visible_but_immutable(self) -> None:
        self._append("essential", 0, "BossDefeatReward_Test", 1)
        item = self.service.player_inventory("player-1")["Containers"]["essential"]["Slots"][0]["Item"]
        self.assertEqual(item["ManagedKind"], "system")
        self.assertIn("system-managed", item["StateFlags"])
        before = self.service.semantic_snapshot()
        with self.assertRaisesRegex(ItemInventoryError, "read-only"):
            self.service.patch_item("player-1", "essential", 0, {"Quantity": 2})
        with self.assertRaisesRegex(ItemInventoryError, "read-only"):
            self.service.delete_item("player-1", "essential", 0, True)
        with self.assertRaisesRegex(ItemInventoryError, "read-only"):
            self.service.move_item("player-1", "essential", 0, "common", 0)
        self.assertEqual(self.service.semantic_snapshot(), before)

    def test_catalog_returns_full_variants_and_excludes_system_records(self) -> None:
        catalog = self.service.catalog()
        group = next(group for group in catalog["Groups"] if len(group["Variants"]) > 1)
        self.assertTrue(all(isinstance(variant, dict) for variant in group["Variants"]))
        self.assertTrue(all(variant["ManagedKind"] == "normal" for variant in group["Variants"]))
        self.assertFalse(any(key.startswith("BossDefeatReward_") for key in catalog["Items"]))


if __name__ == "__main__":
    unittest.main()

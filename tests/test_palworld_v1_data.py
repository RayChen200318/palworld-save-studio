import json
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "palworld_save_studio" / "assets"
DATA = ASSETS / "data"
LOCALES = {"en", "zh-CN", "ja", "fr"}


def load_data(filename: str) -> dict:
    with (DATA / filename).open(encoding="utf-8") as file:
        return json.load(file)


class PalworldV1DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pals = load_data("pal_data.json")
        cls.humans = load_data("human_data.json")
        cls.attacks = load_data("pal_attacks.json")
        cls.passives = load_data("pal_passives.json")
        cls.technologies = load_data("tech_data.json")
        cls.experience = load_data("pal_exp_table.json")

    def test_v1_dataset_sizes(self) -> None:
        public_pals = {
            key: value
            for key, value in self.pals.items()
            if not value.get("Invalid", False)
        }

        self.assertEqual(len(public_pals), 299)
        self.assertEqual(len(self.pals), 696)
        self.assertEqual(len(self.humans), 433)
        self.assertEqual(len(self.attacks), 384)
        self.assertEqual(len(self.passives), 115)
        self.assertEqual(len(self.technologies), 588)
        self.assertEqual(len(self.experience), 100)

    def test_v1_pals_and_variants_are_present(self) -> None:
        expected = {
            "SamuraiDog",
            "CloverFairy",
            "WhiteDeer_Dark",
            "GrassMinotaur_Ice",
            "CactusDoll",
            "DomeArmorDragon",
            "FlowerPrince",
            "KingWhale",
            "WorldTreeDragon",
        }

        self.assertTrue(expected.issubset(self.pals))
        for key in expected:
            self.assertFalse(self.pals[key].get("Invalid", False), key)

    def test_v1_passives_are_present(self) -> None:
        expected = {
            "WorldTree_ATK",
            "WorldTree_DEF",
            "WorldTree_CraftSpeed",
            "WorldTree_FullStomach",
            "WorldTree_Sanity",
            "WorldTree_MoveSpeed",
            "WorldTree_ATK_DEF",
            "Salvation",
            "MutationPal_Babysitter",
            "MutationPal_Mutant",
            "MutationPal_Immortal",
            "MutationPal_ExplosionResist",
            "SelfDeathAddItemDrop_up_3",
            "WorkSuitabilityAddRank_MonsterFarm_2",
            "RideJumpCount_Increase1",
            "RideJumpCount_Increase2",
            "Nocturnal",
            "NightOwl",
            "MiniNushi",
        }

        self.assertTrue(expected.issubset(self.passives))
        self.assertEqual(
            self.passives["MutationPal_Mutant"]["Buff"]["b_Defense"], 0.25
        )
        self.assertEqual(self.passives["Legend"]["Buff"]["b_MoveSpeed"], 0.2)
        self.assertEqual(self.passives["MiniNushi"]["Rating"], 3)
        self.assertEqual(self.passives["MiniNushi"]["Buff"]["b_Defense"], 0.05)

    def test_level_cap_and_v1_technology_levels(self) -> None:
        from palworld_save_studio.core.pal_entity import PalEntity
        from palworld_save_studio.core.player_entity import PlayerEntity

        self.assertEqual(PalEntity.MAX_LEVEL, 80)
        self.assertEqual(PlayerEntity.MAX_LEVEL, 80)
        self.assertIn("80", self.experience)
        self.assertGreater(self.experience["80"]["PalTotalEXP"], 0)
        self.assertEqual(max(item["Level"] for item in self.technologies.values()), 80)

    def test_editable_data_has_all_localizations(self) -> None:
        public_pals = (
            item for item in self.pals.values() if not item.get("Invalid", False)
        )
        for item in public_pals:
            self.assertEqual(set(item["I18n"]), LOCALES, item["InternalName"])
            self.assertTrue(all(item["I18n"].values()), item["InternalName"])

        for collection in (self.attacks, self.passives, self.technologies):
            for item in collection.values():
                self.assertEqual(set(item["I18n"]), LOCALES, item["InternalName"])
                for localized in item["I18n"].values():
                    self.assertTrue(localized["Name"], item["InternalName"])

    def test_v1_pal_and_technology_icons_are_complete(self) -> None:
        pal_icons = ASSETS / "icons" / "pals"
        tech_icons = ASSETS / "icons" / "tech"

        missing_pal_icons = [
            key
            for key, value in self.pals.items()
            if not value.get("Invalid", False) and not (pal_icons / f"{key}.png").is_file()
        ]
        missing_tech_icons = [
            key
            for key in self.technologies
            if not key.startswith("SkillUnlock_")
            and not (tech_icons / f"{key}.png").is_file()
        ]

        self.assertEqual(missing_pal_icons, [])
        self.assertEqual(missing_tech_icons, [])


class AwakeningPropertyTests(unittest.TestCase):
    def test_awakening_can_be_added_and_removed(self) -> None:
        from palworld_save_studio.core.pal_entity import PalEntity
        from palworld_save_studio.utils import LOGGER

        pal = PalEntity.__new__(PalEntity)
        pal._pal_param = {}

        with patch.object(LOGGER, "_print_change"):
            pal.IsAwakening = True
            self.assertTrue(pal.IsAwakening)
            self.assertEqual(
                pal._pal_param["bIsAwakening"],
                {"value": True, "id": None, "type": "BoolProperty"},
            )

            pal.IsAwakening = False
            self.assertFalse(pal.IsAwakening)
            self.assertNotIn("bIsAwakening", pal._pal_param)


if __name__ == "__main__":
    unittest.main()

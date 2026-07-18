import unittest

from palworld_save_studio.core.pal_validation import (
    PalValidationError,
    validate_pal_changes,
)
from palworld_save_studio.utils import DataProvider


class FakePal:
    IsHuman = False
    HasBossVariant = True
    HasTowerVariant = True
    MasteredWaza = []
    EquipWaza = []


class PalValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pal = FakePal()

    def test_accepts_palworld_normal_ranges(self) -> None:
        changes = validate_pal_changes(
            self.pal,
            {
                "Level": 80,
                "FriendshipLevel": 10,
                "Rank": 5,
                "Rank_HP": 20,
                "Talent_HP": 100,
            },
        )
        self.assertEqual(changes["Level"], 80)
        self.assertEqual(changes["Talent_HP"], 100)

    def test_rejects_out_of_range_values(self) -> None:
        for field, value in (
            ("Level", 81),
            ("Rank", 6),
            ("Rank_HP", 21),
            ("Talent_HP", 101),
            ("FriendshipLevel", 11),
        ):
            with self.subTest(field=field):
                with self.assertRaises(PalValidationError):
                    validate_pal_changes(self.pal, {field: value})

    def test_rejects_more_than_four_passives(self) -> None:
        passives = [item["InternalName"] for item in DataProvider.get_sorted_passives()[:5]]
        with self.assertRaisesRegex(PalValidationError, "at most 4"):
            validate_pal_changes(self.pal, {"PassiveSkillList": passives})

    def test_rejects_more_than_three_equipped_skills(self) -> None:
        skills = [item["InternalName"] for item in DataProvider.get_sorted_attacks()[:4]]
        with self.assertRaisesRegex(PalValidationError, "at most 3"):
            validate_pal_changes(
                self.pal,
                {"MasteredWaza": skills, "EquipWaza": skills},
            )

    def test_equipped_skills_must_be_mastered(self) -> None:
        skills = [item["InternalName"] for item in DataProvider.get_sorted_attacks()[:2]]
        with self.assertRaisesRegex(PalValidationError, "also be mastered"):
            validate_pal_changes(
                self.pal,
                {"MasteredWaza": [skills[0]], "EquipWaza": [skills[1]]},
            )

    def test_validates_pal_and_human_species(self) -> None:
        self.assertTrue(DataProvider.is_editable_species("WorldTreeDragon"))
        self.assertTrue(DataProvider.is_editable_species("Hunter_Rifle"))
        self.assertFalse(DataProvider.is_editable_species("BOSS_Hunter_Rifle"))
        self.assertFalse(DataProvider.is_editable_species("not-a-species"))
        invalid_pal = next(
            item["InternalName"]
            for item in DataProvider.get_sorted_pals()
            if item.get("Invalid") and not item.get("Human")
        )
        self.assertFalse(DataProvider.is_editable_species(invalid_pal))


if __name__ == "__main__":
    unittest.main()

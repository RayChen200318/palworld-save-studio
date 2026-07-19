from __future__ import annotations

from typing import Any

from palworld_save_studio.core.pal_entity import PalEntity
from palworld_save_studio.core.pal_objects import PalGender, PalSuitability
from palworld_save_studio.utils import DataProvider


class PalValidationError(ValueError):
    pass


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise PalValidationError(f"{name} must be an integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise PalValidationError(f"{name} must be an integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise PalValidationError(f"{name} must be between {minimum} and {maximum}.")
    return parsed


def _string_list(value: Any, name: str, maximum: int | None = None) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PalValidationError(f"{name} must be a string list.")
    if len(value) != len(set(value)):
        raise PalValidationError(f"{name} cannot contain duplicate entries.")
    if maximum is not None and len(value) > maximum:
        raise PalValidationError(f"{name} can contain at most {maximum} entries.")
    return value


def validate_pal_changes(pal: PalEntity, raw_changes: Any) -> dict[str, Any]:
    if not isinstance(raw_changes, dict) or not raw_changes:
        raise PalValidationError("changes must be a non-empty object.")
    allowed = {
        "CharacterID",
        "NickName",
        "Gender",
        "Level",
        "FriendshipLevel",
        "Rank",
        "Rank_HP",
        "Rank_Attack",
        "Rank_Defence",
        "Rank_CraftSpeed",
        "Talent_HP",
        "Talent_Melee",
        "Talent_Shot",
        "Talent_Defense",
        "PassiveSkillList",
        "MasteredWaza",
        "EquipWaza",
        "Suitabilities",
        "IsBOSS",
        "IsRarePal",
        "IsTower",
        "IsAwakening",
    }
    unknown = sorted(set(raw_changes) - allowed)
    if unknown:
        raise PalValidationError(f"Unsupported fields: {', '.join(unknown)}")

    changes = dict(raw_changes)
    target_species = changes.get("CharacterID")
    target_is_human = pal.IsHuman
    if target_species is not None:
        if not isinstance(target_species, str) or not DataProvider.is_editable_species(target_species):
            raise PalValidationError("CharacterID is not an editable Palworld 1.0 species.")
        target_is_human = bool(DataProvider.is_pal_human(target_species))
    if "NickName" in changes:
        if not isinstance(changes["NickName"], str) or len(changes["NickName"]) > 64:
            raise PalValidationError("NickName must contain at most 64 characters.")
    if "Gender" in changes:
        if changes["Gender"] not in {item.value for item in PalGender}:
            raise PalValidationError("Gender is invalid.")
        if target_is_human:
            raise PalValidationError("Human NPCs do not use the Pal gender field.")

    ranges = {
        "Level": (1, PalEntity.MAX_LEVEL),
        "FriendshipLevel": (-3, 10),
        "Rank": (1, 5),
        "Rank_HP": (0, 20),
        "Rank_Attack": (0, 20),
        "Rank_Defence": (0, 20),
        "Rank_CraftSpeed": (0, 20),
        "Talent_HP": (0, 100),
        "Talent_Melee": (0, 100),
        "Talent_Shot": (0, 100),
        "Talent_Defense": (0, 100),
    }
    for key, (minimum, maximum) in ranges.items():
        if key in changes:
            changes[key] = _integer(changes[key], key, minimum, maximum)

    if "PassiveSkillList" in changes:
        passives = _string_list(changes["PassiveSkillList"], "PassiveSkillList", 4)
        if any(not DataProvider.has_passive_skill(skill) for skill in passives):
            raise PalValidationError("PassiveSkillList contains an unknown skill.")

    if "MasteredWaza" in changes or "EquipWaza" in changes:
        mastered = changes.get("MasteredWaza", pal.MasteredWaza or [])
        equipped = changes.get("EquipWaza", pal.EquipWaza or [])
        mastered = _string_list(mastered, "MasteredWaza")
        equipped = _string_list(equipped, "EquipWaza", 3)
        if any(not DataProvider.has_attack(skill) for skill in [*mastered, *equipped]):
            raise PalValidationError("Active skill list contains an unknown skill.")
        if not set(equipped).issubset(mastered):
            raise PalValidationError("Every equipped skill must also be mastered.")

    if "Suitabilities" in changes:
        suits = changes["Suitabilities"]
        if not isinstance(suits, dict):
            raise PalValidationError("Suitabilities must be an object.")
        species = target_species or getattr(pal, "DataAccessKey", None) or getattr(
            pal, "RawSpecieKey", None
        )
        base_suits = DataProvider.get_pal_suitabilities(species) or {}
        target_rank = changes.get("Rank", getattr(pal, "Rank", 1) or 1)
        full_rank_bonus = 1 if target_rank >= 5 else 0
        normalized: dict[str, int] = {}
        for key, value in suits.items():
            if PalSuitability.from_value(key) is None:
                raise PalValidationError(f"Unknown work suitability: {key}")
            base_rank = base_suits.get(key, 0)
            if base_rank <= 0:
                raise PalValidationError(
                    f"The selected species does not have work suitability: {key}"
                )
            legal_minimum = min(10, base_rank + full_rank_bonus)
            normalized[key] = _integer(value, key, legal_minimum, 10)
        changes["Suitabilities"] = normalized

    for key in ("IsBOSS", "IsRarePal", "IsTower", "IsAwakening"):
        if key in changes and not isinstance(changes[key], bool):
            raise PalValidationError(f"{key} must be a boolean.")
    if changes.get("IsBOSS"):
        species = target_species or pal.RawSpecieKey
        if not DataProvider.has_x_variant_pal(species, "BOSS"):
            raise PalValidationError("This species has no Boss variant.")
    if changes.get("IsTower"):
        species = target_species or pal.RawSpecieKey
        if not DataProvider.has_x_variant_pal(species, "GYM"):
            raise PalValidationError("This species has no tower variant.")
    if target_is_human and any(changes.get(key) for key in ("IsBOSS", "IsRarePal", "IsTower")):
        raise PalValidationError("Human NPCs cannot use Pal variant flags.")
    return changes

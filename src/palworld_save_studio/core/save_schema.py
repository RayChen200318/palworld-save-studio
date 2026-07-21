from __future__ import annotations

from typing import Any

from palworld_save_studio.core.pal_objects import PalObjects


class SaveSchemaError(ValueError):
    """Raised when an editable field no longer matches Palworld's GVAS schema."""


def _expect_integer_range(
    value: Any,
    minimum: int,
    maximum: int,
    *,
    label: str,
) -> None:
    if value is None:
        return
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
        or value > maximum
    ):
        raise SaveSchemaError(
            f"{label} must be an integer between {minimum} and {maximum}."
        )


def _expect_text_length(value: Any, maximum: int, *, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or len(value) > maximum:
        raise SaveSchemaError(f"{label} must contain at most {maximum} characters.")


def _expect_property(
    container: dict[str, Any],
    key: str,
    property_type: str,
    *,
    array_type: str | None = None,
    owner: str,
) -> None:
    if key not in container:
        return
    value = container[key]
    actual = value.get("type") if isinstance(value, dict) else None
    if actual != property_type:
        raise SaveSchemaError(
            f"{owner}.{key} must be {property_type}, found {actual or 'invalid data'}."
        )
    if array_type is not None and value.get("array_type") != array_type:
        raise SaveSchemaError(
            f"{owner}.{key} must contain {array_type}, found "
            f"{value.get('array_type') or 'invalid data'}."
        )


def validate_player_schema(player: Any) -> None:
    owner = f"Player[{player.PlayerUId}]"
    for key, property_type in {
        "NickName": "StrProperty",
        "UnusedStatusPoint": "UInt16Property",
        "Level": "ByteProperty",
        "Exp": "Int64Property",
    }.items():
        _expect_property(player._player_param, key, property_type, owner=owner)
    for key in ("GotStatusPointList", "GotExStatusPointList"):
        _expect_property(
            player._player_param,
            key,
            "ArrayProperty",
            array_type="StructProperty",
            owner=owner,
        )

    for key in ("TechnologyPoint", "bossTechnologyPoint"):
        _expect_property(player._player_save_data, key, "IntProperty", owner=owner)
    _expect_property(
        player._player_save_data,
        "UnlockedRecipeTechnologyNames",
        "ArrayProperty",
        array_type="NameProperty",
        owner=owner,
    )

    unused = player.UnusedStatusPoint
    _expect_integer_range(
        unused,
        PalObjects.UInt16Min,
        PalObjects.UInt16Max,
        label=f"{owner}.UnusedStatusPoint",
    )
    _expect_integer_range(player.Level, 1, player.MAX_LEVEL, label=f"{owner}.Level")
    _expect_integer_range(player.Exp, 0, (1 << 63) - 1, label=f"{owner}.Exp")
    _expect_integer_range(
        player.TechnologyPoint,
        0,
        (1 << 31) - 1,
        label=f"{owner}.TechnologyPoint",
    )
    _expect_integer_range(
        player.bossTechnologyPoint,
        0,
        (1 << 31) - 1,
        label=f"{owner}.bossTechnologyPoint",
    )
    _expect_text_length(player.NickName, 64, label=f"{owner}.NickName")

    individual = player._player_save_data.get("IndividualId", {}).get("value", {})
    player_uid = PalObjects.get_BaseType(individual.get("PlayerUId"))
    instance_id = PalObjects.get_BaseType(individual.get("InstanceId"))
    if player_uid != player.PlayerUId:
        raise SaveSchemaError(f"{owner} has a mismatched PlayerUId in the player save.")
    if instance_id != player.InstanceId:
        raise SaveSchemaError(f"{owner} has a mismatched InstanceId in the player save.")


def validate_pal_schema(pal: Any) -> None:
    owner = f"Pal[{pal.InstanceId}]"
    expected = {
        "CharacterID": "NameProperty",
        "NickName": "StrProperty",
        "FilteredNickName": "StrProperty",
        "Gender": "EnumProperty",
        "Level": "ByteProperty",
        "Exp": "Int64Property",
        "FriendshipPoint": "IntProperty",
        "Rank": "ByteProperty",
        "Rank_HP": "ByteProperty",
        "Rank_Attack": "ByteProperty",
        "Rank_Defence": "ByteProperty",
        "Rank_CraftSpeed": "ByteProperty",
        "Talent_HP": "ByteProperty",
        "Talent_Melee": "ByteProperty",
        "Talent_Shot": "ByteProperty",
        "Talent_Defense": "ByteProperty",
        "IsRarePal": "BoolProperty",
        "bIsAwakening": "BoolProperty",
        "Hp": "StructProperty",
        "SanityValue": "FloatProperty",
        "FullStomach": "FloatProperty",
        "SkinName": "NameProperty",
        "UniqueNPCID": "NameProperty",
    }
    for key, property_type in expected.items():
        _expect_property(pal._pal_param, key, property_type, owner=owner)
    for key, array_type in {
        "PassiveSkillList": "NameProperty",
        "MasteredWaza": "EnumProperty",
        "EquipWaza": "EnumProperty",
        "GotWorkSuitabilityAddRankList": "StructProperty",
    }.items():
        _expect_property(
            pal._pal_param,
            key,
            "ArrayProperty",
            array_type=array_type,
            owner=owner,
        )

    _expect_text_length(pal.NickName, 64, label=f"{owner}.NickName")
    _expect_integer_range(pal.Level, 1, pal.MAX_LEVEL, label=f"{owner}.Level")
    _expect_integer_range(pal.Exp, 0, (1 << 63) - 1, label=f"{owner}.Exp")
    _expect_integer_range(pal.Rank, 1, 5, label=f"{owner}.Rank")
    for key in ("Rank_HP", "Rank_Attack", "Rank_Defence", "Rank_CraftSpeed"):
        _expect_integer_range(
            getattr(pal, key), 0, 20, label=f"{owner}.{key}"
        )
    for key in ("Talent_HP", "Talent_Melee", "Talent_Shot", "Talent_Defense"):
        _expect_integer_range(
            getattr(pal, key), 0, 100, label=f"{owner}.{key}"
        )
    passive_skills = pal.PassiveSkillList
    equipped_skills = pal.EquipWaza
    if passive_skills is not None and len(passive_skills) > 4:
        raise SaveSchemaError(f"{owner}.PassiveSkillList contains more than four entries.")
    if equipped_skills is not None and len(equipped_skills) > 3:
        raise SaveSchemaError(f"{owner}.EquipWaza contains more than three entries.")


def validate_editable_schema(manager: Any) -> None:
    for player in manager.get_players():
        validate_player_schema(player)
    for context in manager.get_all_pal_contexts():
        validate_pal_schema(context["pal"])
    if manager.item_inventory is not None:
        manager.item_inventory.validate_integrity()

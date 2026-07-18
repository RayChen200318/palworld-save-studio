from __future__ import annotations

import json
import traceback
from typing import Any

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_save_studio.core import PalEntity, SaveManager
from palworld_save_studio.core.pal_objects import PalObjects
from palworld_save_studio.core.pal_validation import (
    PalValidationError,
    validate_pal_changes,
)
from palworld_save_studio.utils import DataProvider, LOGGER
from palworld_save_studio.utils.util import reply


pal_blueprint = Blueprint("pal", __name__)


def _context(instance_id: str) -> dict[str, Any] | None:
    return SaveManager().get_pal_context(instance_id)


def _state_flags(pal: PalEntity, location: str) -> list[str]:
    flags: list[str] = []
    if pal.is_unreferenced_pal or location == "outside":
        flags.append("outside-container")
    if pal.HasWorkerSick:
        flags.append("sick")
    if pal.IsFaintedPal:
        flags.append("fainted")
    if pal.IsExpeditionPal:
        flags.append("expedition")
    if pal.IsBOSS:
        flags.append("boss")
    if pal.IsRarePal:
        flags.append("lucky")
    if pal.IsTower:
        flags.append("tower")
    if pal.IsAwakening:
        flags.append("awakening")
    return flags


def _pal_summary(context: dict[str, Any]) -> dict[str, Any]:
    pal: PalEntity = context["pal"]
    owner = context.get("owner")
    species_key = pal.DataAccessKey or pal.RawSpecieKey or pal.CharacterID
    return {
        "InstanceId": str(pal.InstanceId),
        "CharacterID": pal.CharacterID,
        "SpeciesKey": species_key,
        "SpeciesName": pal.I18nName or pal.DisplayName or species_key,
        "NickName": pal.NickName or "",
        "IconAccessKey": pal.IconAccessKey or "unknown",
        "PalDeckId": pal.PalDeckID or "",
        "Level": pal.Level or 1,
        "Gender": pal.Gender.value if pal.Gender else None,
        "OwnerPlayerUId": str(owner.PlayerUId) if owner else None,
        "OwnerName": owner.NickName if owner else None,
        "ObjectType": "human" if pal.IsHuman else "pal",
        "Location": context["location"],
        "Elements": DataProvider.get_pal_elements(species_key) or [],
        "StateFlags": _state_flags(pal, context["location"]),
        "IsAnomalous": bool(
            pal.is_unreferenced_pal
            or pal.HasWorkerSick
            or pal.IsFaintedPal
            or context["location"] == "outside"
        ),
    }


def _pal_data(context: dict[str, Any]) -> dict[str, Any]:
    pal: PalEntity = context["pal"]
    summary = _pal_summary(context)
    summary.update(
        {
            "group_id": str(pal.group_id) if pal.group_id else None,
            "ContainerId": str(pal.ContainerId) if pal.ContainerId else None,
            "SlotIndex": pal.SlotIndex,
            "DataAccessKey": pal.DataAccessKey,
            "DisplayName": pal.DisplayName,
            "FriendshipLevel": pal.FriendshipLevel if pal.FriendshipLevel is not None else 0,
            "HasBaseVariant": pal.HasBaseVariant,
            "HasBossVariant": pal.HasBossVariant,
            "HasTowerVariant": pal.HasTowerVariant,
            "HasWorkerSick": pal.HasWorkerSick,
            "IsFaintedPal": pal.IsFaintedPal,
            "Is_Unref_Pal": pal.is_unreferenced_pal,
            "in_owner_palbox": pal.in_owner_palbox,
            "IsHuman": pal.IsHuman,
            "IsBOSS": bool(pal.IsBOSS),
            "IsRarePal": bool(pal.IsRarePal),
            "IsTower": bool(pal.IsTower),
            "IsRAID": bool(pal.IsRAID),
            "IsPREDATOR": bool(pal.IsPREDATOR),
            "IsOilrig": bool(pal.IsOilrig),
            "IsExpeditionPal": bool(pal.IsExpeditionPal),
            "IsAwakening": bool(pal.IsAwakening),
            "ComputedMaxHP": pal.ComputedMaxHP,
            "ComputedAttack": pal.ComputedAttack,
            "ComputedDefense": pal.ComputedDefense,
            "ComputedCraftSpeed": pal.ComputedCraftSpeed,
            "Rank": pal.Rank or 1,
            "Rank_HP": pal.Rank_HP or 0,
            "Rank_Attack": pal.Rank_Attack or 0,
            "Rank_Defence": pal.Rank_Defence or 0,
            "Rank_CraftSpeed": pal.Rank_CraftSpeed or 0,
            "Talent_HP": pal.Talent_HP or 0,
            "Talent_Melee": pal.Talent_Melee or 0,
            "Talent_Shot": pal.Talent_Shot or 0,
            "Talent_Defense": pal.Talent_Defense or 0,
            "PassiveSkillList": list(pal.PassiveSkillList or []),
            "EquipWaza": list(pal.EquipWaza or []),
            "MasteredWaza": list(pal.MasteredWaza or []),
            "Suitabilities": pal.WorkSuitabilities or {},
        }
    )
    return summary


def _set_array(pal: PalEntity, key: str, values: list[str], array_type: str) -> None:
    current = PalObjects.get_ArrayProperty(pal._pal_param.get(key))
    if current is None:
        pal._pal_param[key] = PalObjects.ArrayProperty(array_type, {"values": list(values)})
    else:
        current[:] = values
    if not values:
        pal._pal_param.pop(key, None)


def _apply_changes(pal: PalEntity, changes: dict[str, Any]) -> None:
    if "CharacterID" in changes:
        pal.CharacterID = changes["CharacterID"]
    for key in (
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
    ):
        if key in changes:
            setattr(pal, key, changes[key])
    if "PassiveSkillList" in changes:
        _set_array(pal, "PassiveSkillList", changes["PassiveSkillList"], "NameProperty")
    if "MasteredWaza" in changes:
        _set_array(pal, "MasteredWaza", changes["MasteredWaza"], "EnumProperty")
    if "EquipWaza" in changes:
        _set_array(pal, "EquipWaza", changes["EquipWaza"], "EnumProperty")
    if "Suitabilities" in changes:
        for suitability, rank in changes["Suitabilities"].items():
            pal.set_WorkSuitability(suitability, rank)
    for key in ("IsBOSS", "IsRarePal", "IsTower", "IsAwakening"):
        if key in changes:
            setattr(pal, key, changes[key])


@pal_blueprint.route("/list", methods=["GET"])
@jwt_required()
def list_pals():
    items = [_pal_summary(context) for context in SaveManager().get_all_pal_contexts()]
    items.sort(key=lambda item: (item["ObjectType"] == "human", item["PalDeckId"], item["SpeciesName"], item["InstanceId"]))
    return reply(0, items)


@pal_blueprint.route("/<instance_id>", methods=["GET"])
@jwt_required()
def get_pal(instance_id: str):
    context = _context(instance_id)
    if not context:
        return reply(1, msg=f"Pal {instance_id} was not found."), 404
    return reply(0, _pal_data(context))


@pal_blueprint.route("/<instance_id>", methods=["PATCH"])
@jwt_required()
def patch_pal(instance_id: str):
    context = _context(instance_id)
    if not context:
        return reply(1, msg=f"Pal {instance_id} was not found."), 404
    try:
        changes = validate_pal_changes(context["pal"], (request.get_json(silent=True) or {}).get("changes"))
        _apply_changes(context["pal"], changes)
        revision = SaveManager().mark_dirty()
        refreshed = SaveManager().get_pal_context(instance_id)
        return reply(0, {"Pal": _pal_data(refreshed), "DirtyRevision": revision})
    except PalValidationError as exc:
        return reply(1, msg=str(exc)), 400
    except Exception:
        LOGGER.error(f"Failed patching Pal: {traceback.format_exc()}")
        return reply(1, msg="The Pal could not be updated."), 500


@pal_blueprint.route("/<instance_id>", methods=["DELETE"])
@jwt_required()
def delete_pal(instance_id: str):
    if not SaveManager().delete_pal(instance_id):
        return reply(1, msg=f"Pal {instance_id} could not be deleted."), 404
    return reply(0, {"DirtyRevision": SaveManager().mark_dirty()})


@pal_blueprint.route("", methods=["POST"])
@jwt_required()
def create_pal():
    payload = request.get_json(silent=True) or {}
    player_uid = payload.get("OwnerPlayerUId")
    character_id = payload.get("CharacterID")
    if not player_uid or not SaveManager().get_player(player_uid):
        return reply(1, msg="OwnerPlayerUId is invalid."), 400
    if not isinstance(character_id, str) or not DataProvider.is_editable_species(character_id):
        return reply(1, msg="CharacterID is not an editable Palworld 1.0 species."), 400
    pal = SaveManager().add_pal(player_uid, character_id=character_id)
    if not pal:
        return reply(1, msg="The selected player's Palbox has no free slot."), 409
    revision = SaveManager().mark_dirty()
    return reply(0, {"Pal": _pal_data(SaveManager().get_pal_context(str(pal.InstanceId))), "DirtyRevision": revision})


@pal_blueprint.route("/<instance_id>/duplicate", methods=["POST"])
@jwt_required()
def duplicate_pal(instance_id: str):
    context = _context(instance_id)
    if not context:
        return reply(1, msg=f"Pal {instance_id} was not found."), 404
    owner = context.get("owner")
    if not owner:
        return reply(1, msg="Choose an owner before duplicating this object."), 409
    duplicated = SaveManager().add_pal(str(owner.PlayerUId), context["pal"]._pal_obj)
    if not duplicated:
        return reply(1, msg="The selected player's Palbox has no free slot."), 409
    revision = SaveManager().mark_dirty()
    return reply(0, {"Pal": _pal_data(SaveManager().get_pal_context(str(duplicated.InstanceId))), "DirtyRevision": revision})


@pal_blueprint.route("/<instance_id>/retrieve", methods=["POST"])
@jwt_required()
def retrieve_pal(instance_id: str):
    context = _context(instance_id)
    if not context:
        return reply(1, msg=f"Pal {instance_id} was not found."), 404
    owner = context.get("owner")
    if not owner:
        return reply(1, msg="This object has no recoverable owner."), 409
    if context["location"] == "palbox":
        return reply(0, {"Pal": _pal_data(context), "DirtyRevision": SaveManager()._dirty_revision})
    if not SaveManager().retrieve_pal(instance_id, owner.PlayerUId):
        return reply(1, msg="The owner's Palbox has no free slot."), 409
    revision = SaveManager().mark_dirty()
    return reply(0, {"Pal": _pal_data(SaveManager().get_pal_context(instance_id)), "DirtyRevision": revision})


@pal_blueprint.route("/heal-all", methods=["POST"])
@jwt_required()
def heal_all():
    healed = SaveManager().heal_all_pals()
    return reply(0, {"Healed": healed, "DirtyRevision": SaveManager().mark_dirty()})


@pal_blueprint.route("/<instance_id>/raw", methods=["GET"])
@jwt_required()
def raw_pal(instance_id: str):
    context = _context(instance_id)
    if not context:
        return reply(1, msg=f"Pal {instance_id} was not found."), 404
    return reply(0, {"Json": json.dumps(json.loads(context["pal"].dump_obj()), ensure_ascii=False, indent=2)})

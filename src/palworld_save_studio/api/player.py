from __future__ import annotations

from contextlib import contextmanager
import copy
import traceback
from typing import Any, Iterator

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_save_studio.core import SaveManager
from palworld_save_studio.core.pal_objects import PalObjects
from palworld_save_studio.core.player_entity import PlayerEntity
from palworld_save_studio.utils import DataProvider, LOGGER
from palworld_save_studio.utils.util import reply


player_blueprint = Blueprint("player", __name__)


def _player_data(player: PlayerEntity, *, include_technology: bool = False) -> dict[str, Any]:
    result = {
        "PlayerUId": str(player.PlayerUId),
        "InstanceId": str(player.InstanceId),
        "NickName": player.NickName or "",
        "Level": player.Level or 1,
        "HasViewingCage": player.has_viewing_cage(),
        "OtomoCharacterContainerId": str(player.OtomoCharacterContainerId),
        "PalStorageContainerId": str(player.PalStorageContainerId),
        "TechnologyPoint": player.TechnologyPoint or 0,
        "BossTechnologyPoint": player.bossTechnologyPoint or 0,
        "PalCount": len(player._palbox),
    }
    if include_technology:
        result["UnlockedRecipeTechnologyNames"] = list(
            player.UnlockedRecipeTechnologyNames or []
        )
    return result


def _find_player(player_id: str) -> PlayerEntity | None:
    return SaveManager().get_player(player_id)


def _bounded_integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return parsed


@contextmanager
def _atomic_player(player: PlayerEntity) -> Iterator[None]:
    """Restore both Level.sav and player-SAV data if a player edit fails."""

    parameter_backup = copy.deepcopy(player._player_param)
    save_data_backup = copy.deepcopy(player._player_save_data)
    try:
        yield
    except Exception:
        player._player_param.clear()
        player._player_param.update(parameter_backup)
        player._player_save_data.clear()
        player._player_save_data.update(save_data_backup)
        raise


def _validated_player_changes(
    player: PlayerEntity, changes: Any
) -> dict[str, Any]:
    if not isinstance(changes, dict) or not changes:
        raise ValueError("changes must be a non-empty object.")
    allowed = {
        "NickName",
        "Level",
        "TechnologyPoint",
        "BossTechnologyPoint",
        "HasViewingCage",
    }
    unknown = sorted(set(changes) - allowed)
    if unknown:
        raise ValueError(f"Unsupported fields: {', '.join(unknown)}")

    validated: dict[str, Any] = {}
    if "NickName" in changes:
        nickname = changes["NickName"]
        if not isinstance(nickname, str) or len(nickname) > 64:
            raise ValueError("NickName must contain at most 64 characters.")
        validated["NickName"] = nickname
    if "Level" in changes:
        target_level = _bounded_integer(
            changes["Level"], "Level", 1, PlayerEntity.MAX_LEVEL
        )
        status_points = (player.UnusedStatusPoint or 0) + target_level - (player.Level or 1)
        if status_points < PalObjects.UInt16Min:
            raise ValueError(
                "The player does not have enough status points to lower to that level."
            )
        if status_points > PalObjects.UInt16Max:
            raise ValueError("UnusedStatusPoint would exceed the UInt16 save range.")
        validated["Level"] = target_level
    if "TechnologyPoint" in changes:
        validated["TechnologyPoint"] = _bounded_integer(
            changes["TechnologyPoint"], "TechnologyPoint", 0, 9999
        )
    if "BossTechnologyPoint" in changes:
        validated["BossTechnologyPoint"] = _bounded_integer(
            changes["BossTechnologyPoint"], "BossTechnologyPoint", 0, 9999
        )
    if "HasViewingCage" in changes:
        enabled = changes["HasViewingCage"]
        if not isinstance(enabled, bool):
            raise ValueError("HasViewingCage must be a boolean.")
        validated["HasViewingCage"] = enabled
    return validated


@player_blueprint.route("", methods=["GET"])
@jwt_required()
def list_players():
    players = sorted(SaveManager().get_players(), key=lambda item: (item.NickName or "", str(item.PlayerUId)))
    return reply(0, [_player_data(player) for player in players])


@player_blueprint.route("/<player_id>", methods=["GET"])
@jwt_required()
def get_player(player_id: str):
    player = _find_player(player_id)
    if not player:
        return reply(1, msg=f"Player {player_id} was not found."), 404
    return reply(0, _player_data(player, include_technology=True))


@player_blueprint.route("/<player_id>", methods=["PATCH"])
@jwt_required()
def patch_player(player_id: str):
    player = _find_player(player_id)
    if not player:
        return reply(1, msg=f"Player {player_id} was not found."), 404
    try:
        changes = _validated_player_changes(
            player, (request.get_json(silent=True) or {}).get("changes")
        )
        with _atomic_player(player):
            if "NickName" in changes:
                player.NickName = changes["NickName"]
            if "Level" in changes:
                player.Level = changes["Level"]
                if player.Level != changes["Level"]:
                    raise ValueError(
                        "The player does not have enough status points to lower to that level."
                    )
            if "TechnologyPoint" in changes:
                player.TechnologyPoint = changes["TechnologyPoint"]
            if "BossTechnologyPoint" in changes:
                player.bossTechnologyPoint = changes["BossTechnologyPoint"]
            if "HasViewingCage" in changes:
                player.toggle_UnlockedRecipeTechnologyNames(
                    "DisplayCharacter", changes["HasViewingCage"]
                )
        revision = SaveManager().mark_dirty()
        return reply(0, {"Player": _player_data(player, include_technology=True), "DirtyRevision": revision})
    except ValueError as exc:
        return reply(1, msg=str(exc)), 400
    except Exception:
        LOGGER.error(f"Failed patching player: {traceback.format_exc()}")
        return reply(1, msg="The player could not be updated."), 500


@player_blueprint.route("/<player_id>/technology/<technology_id>", methods=["PATCH"])
@jwt_required()
def patch_technology(player_id: str, technology_id: str):
    player = _find_player(player_id)
    if not player:
        return reply(1, msg=f"Player {player_id} was not found."), 404
    if technology_id not in DataProvider.get_tech_data():
        return reply(1, msg=f"Technology {technology_id} is unknown."), 400
    enabled = (request.get_json(silent=True) or {}).get("Enabled")
    if not isinstance(enabled, bool):
        return reply(1, msg="Enabled must be a boolean."), 400
    with _atomic_player(player):
        player.toggle_UnlockedRecipeTechnologyNames(technology_id, enabled)
    return reply(
        0,
        {
            "Technology": technology_id,
            "Enabled": enabled,
            "DirtyRevision": SaveManager().mark_dirty(),
        },
    )


@player_blueprint.route("/<player_id>/technology/unlock-all", methods=["POST"])
@jwt_required()
def unlock_all_technology(player_id: str):
    player = _find_player(player_id)
    if not player:
        return reply(1, msg=f"Player {player_id} was not found."), 404
    with _atomic_player(player):
        player.unlock_all_techs()
    return reply(0, {"Player": _player_data(player, include_technology=True), "DirtyRevision": SaveManager().mark_dirty()})

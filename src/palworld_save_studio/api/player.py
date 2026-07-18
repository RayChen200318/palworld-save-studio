from __future__ import annotations

import traceback
from typing import Any

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_save_studio.core import SaveManager
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
    changes = (request.get_json(silent=True) or {}).get("changes")
    if not isinstance(changes, dict) or not changes:
        return reply(1, msg="changes must be a non-empty object."), 400
    allowed = {"NickName", "Level", "TechnologyPoint", "BossTechnologyPoint", "HasViewingCage"}
    unknown = sorted(set(changes) - allowed)
    if unknown:
        return reply(1, msg=f"Unsupported fields: {', '.join(unknown)}"), 400
    try:
        if "NickName" in changes:
            nickname = changes["NickName"]
            if not isinstance(nickname, str) or len(nickname) > 64:
                raise ValueError("NickName must contain at most 64 characters.")
            player.NickName = nickname
        if "Level" in changes:
            target_level = _bounded_integer(changes["Level"], "Level", 1, PlayerEntity.MAX_LEVEL)
            player.Level = target_level
            if player.Level != target_level:
                raise ValueError("The player does not have enough status points to lower to that level.")
        if "TechnologyPoint" in changes:
            player.TechnologyPoint = _bounded_integer(changes["TechnologyPoint"], "TechnologyPoint", 0, 9999)
        if "BossTechnologyPoint" in changes:
            player.bossTechnologyPoint = _bounded_integer(changes["BossTechnologyPoint"], "BossTechnologyPoint", 0, 9999)
        if "HasViewingCage" in changes:
            enabled = changes["HasViewingCage"]
            if not isinstance(enabled, bool):
                raise ValueError("HasViewingCage must be a boolean.")
            player.toggle_UnlockedRecipeTechnologyNames("DisplayCharacter", enabled)
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
    player.unlock_all_techs()
    return reply(0, {"Player": _player_data(player, include_technology=True), "DirtyRevision": SaveManager().mark_dirty()})

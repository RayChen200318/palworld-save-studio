from __future__ import annotations

import traceback
from typing import Any, Callable

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_save_studio.core import SaveManager
from palworld_save_studio.core.item_inventory import (
    ItemInventoryError,
    ItemInventoryService,
)
from palworld_save_studio.utils import LOGGER
from palworld_save_studio.utils.util import reply


item_blueprint = Blueprint("item", __name__)


def _payload() -> dict[str, Any]:
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}


def _service():
    manager = SaveManager()
    if not manager._loaded or manager.item_inventory is None:
        raise ItemInventoryError("Load a save before managing items.")
    return manager.item_inventory


def _mutate(operation: Callable[[], dict[str, Any]]):
    try:
        inventory = operation()
        revision = SaveManager().mark_dirty()
        return reply(0, {"Inventory": inventory, "DirtyRevision": revision})
    except ItemInventoryError as exc:
        return reply(1, msg=str(exc)), 409
    except Exception:
        LOGGER.error(f"Item operation failed: {traceback.format_exc()}")
        return reply(1, msg="The item operation could not be completed."), 500


@item_blueprint.route("/catalog", methods=["GET"])
@jwt_required()
def get_catalog():
    try:
        return reply(0, ItemInventoryService.catalog())
    except Exception:
        LOGGER.error(f"Item catalog failed: {traceback.format_exc()}")
        return reply(1, msg="The offline item catalog could not be loaded."), 500


@item_blueprint.route("/player/<player_id>", methods=["GET"])
@jwt_required()
def get_player_inventory(player_id: str):
    try:
        return reply(0, _service().player_inventory(player_id))
    except ItemInventoryError as exc:
        return reply(1, msg=str(exc)), 404
    except Exception:
        LOGGER.error(f"Item inventory failed: {traceback.format_exc()}")
        return reply(1, msg="The player's item inventory could not be loaded."), 500


@item_blueprint.route("/player/<player_id>", methods=["POST"])
@jwt_required()
def create_item(player_id: str):
    payload = _payload()
    return _mutate(
        lambda: _service().add_item(
            player_id,
            payload.get("StaticId"),
            payload.get("Container"),
            payload.get("Quantity", 1),
            payload.get("SlotIndex"),
            payload.get("EggCharacterId"),
        )
    )


@item_blueprint.route(
    "/player/<player_id>/<container>/<int:slot_index>", methods=["PATCH"]
)
@jwt_required()
def patch_item(player_id: str, container: str, slot_index: int):
    payload = _payload()
    changes = payload.get("changes", payload)
    return _mutate(
        lambda: _service().patch_item(player_id, container, slot_index, changes)
    )


@item_blueprint.route(
    "/player/<player_id>/<container>/<int:slot_index>", methods=["DELETE"]
)
@jwt_required()
def delete_item(player_id: str, container: str, slot_index: int):
    payload = _payload()
    return _mutate(
        lambda: _service().delete_item(
            player_id,
            container,
            slot_index,
            payload.get("ConfirmDangerous") is True,
        )
    )


@item_blueprint.route("/player/<player_id>/move", methods=["POST"])
@jwt_required()
def move_item(player_id: str):
    payload = _payload()
    source_value = payload.get("Source")
    target_value = payload.get("Target")
    source = source_value if isinstance(source_value, dict) else {}
    target = target_value if isinstance(target_value, dict) else {}
    return _mutate(
        lambda: _service().move_item(
            player_id,
            source.get("Container"),
            source.get("SlotIndex"),
            target.get("Container"),
            target.get("SlotIndex"),
        )
    )

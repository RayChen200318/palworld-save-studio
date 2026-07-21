import os
from pathlib import Path
import traceback
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from palworld_save_studio.config import (
    PROGRAM_PATH,
    Config,
    version_info,
    is_gh_build,
)
from palworld_save_studio.core import SaveManager
from palworld_save_studio.core.save_transaction import SaveTransactionError
from palworld_save_studio.utils import LOGGER, DataProvider
from palworld_save_studio.utils.util import get_path_context, reply

save_blueprint = Blueprint("save", __name__)

PATH_NOT_FOUND_ERRORS = {2, 3, 15, 53, 64, 67, 1231}
PATH_PERMISSION_ERRORS = {5, 65, 1326}
PATH_INVALID_ERRORS = {123, 161}


def _path_error_response(exc: Exception):
    winerror = getattr(exc, "winerror", None)
    if isinstance(exc, PermissionError) or winerror in PATH_PERMISSION_ERRORS:
        return reply(1, msg="Permission denied while opening this directory."), 403
    if isinstance(exc, FileNotFoundError) or winerror in PATH_NOT_FOUND_ERRORS:
        return reply(1, msg="The path does not exist or the network location is unavailable."), 404
    if isinstance(exc, (TypeError, ValueError, NotADirectoryError)) or winerror in PATH_INVALID_ERRORS:
        return reply(1, msg="The path must be an absolute directory."), 400
    LOGGER.error(f"Directory browser error: {exc!r}")
    return reply(1, msg="The directory could not be opened."), 500


def _open_path_context(path: Path):
    context = get_path_context(path)
    Config.path = context["currentPath"]
    return reply(0, context)


@save_blueprint.route("/fetch_config", methods=["GET"])
def fetch_config():
    return reply(
        0,
        {
            "I18n": Config.i18n,
            "I18nList": DataProvider.get_i18n_map(),
            "Path": Config.path,
            "HasPassword": Config.password != None,
            "VERSION": version_info(),
            "IsOfficialBuild": is_gh_build(),
            "BackupEnabled": Config.backup_enabled,
        },
    )


@save_blueprint.route("/load", methods=["POST"])
# @LOGGER.api_logger
@jwt_required()
def load():
    payload = request.get_json(silent=True) or {}
    path = payload.get("ReadPath", None)
    save_kind = payload.get("SaveKind")
    if save_kind not in {"local", "dedicated"}:
        return reply(1, msg="SaveKind must be 'local' or 'dedicated'."), 400
    path = path or Config.path
    manager = SaveManager()
    if manager.has_draft:
        return reply(
            1,
            msg="Discard the current in-memory draft before loading another save.",
        ), 409
    state = manager._capture_runtime_state()
    try:
        if path and manager.open(path, save_kind=save_kind):
            Config.path = str(Path(path).resolve())
            Config.save_to_file()
            return reply(0, manager.session_summary())
    except SaveTransactionError as exc:
        LOGGER.error(f"Rejected save structure: {traceback.format_exc()}")
        manager._restore_runtime_state(state)
        return reply(1, msg=str(exc)), 400
    except Exception:
        stack_trace = traceback.format_exc()
        LOGGER.error(f"Error Loading Save {stack_trace}")
        manager._restore_runtime_state(state)
        return reply(
            1,
            msg="The save could not be parsed. Confirm that it is a Palworld 1.0 save and that the game is closed.",
        ), 400

    manager._restore_runtime_state(state)
    LOGGER.warning(f"Failed to load, check path: {path}")
    return reply(1, None, f"No Palworld save was found at: {path}"), 400


@save_blueprint.route("/session", methods=["GET"])
@jwt_required()
def get_session():
    return reply(0, SaveManager().session_summary())


@save_blueprint.route("/discard", methods=["POST"])
@jwt_required()
def discard():
    if SaveManager().discard():
        return reply(0, SaveManager().session_summary())
    return reply(1, msg="The in-memory draft could not be discarded."), 500


@save_blueprint.route("/commit", methods=["POST"])
@jwt_required()
def commit():
    try:
        payload = request.get_json(silent=True) or {}
        result = SaveManager().commit(
            server_stopped_confirmed=payload.get("ServerStoppedConfirmed") is True
        )
        return reply(0, {"Commit": result, "Session": SaveManager().session_summary()})
    except SaveTransactionError as exc:
        LOGGER.error(f"Save commit failed: {traceback.format_exc()}")
        return reply(1, msg=str(exc)), 409
    except Exception:
        stack_trace = traceback.format_exc()
        LOGGER.error(f"Save commit failed: {stack_trace}")
        return reply(1, msg="The save could not be committed."), 500


@save_blueprint.route("/commit-preview", methods=["GET"])
@jwt_required()
def commit_preview():
    try:
        return reply(0, SaveManager().commit_preview())
    except SaveTransactionError as exc:
        LOGGER.error(f"Save preview failed: {traceback.format_exc()}")
        return reply(1, msg=str(exc)), 409
    except Exception:
        LOGGER.error(f"Save preview failed: {traceback.format_exc()}")
        return reply(1, msg="The save could not be validated."), 500


@save_blueprint.route("/settings", methods=["PATCH"])
@jwt_required()
def update_settings():
    payload = request.get_json(silent=True) or {}
    enabled = payload.get("BackupEnabled")
    if not isinstance(enabled, bool):
        return reply(1, msg="BackupEnabled must be a boolean."), 400
    if SaveManager()._save_kind == "dedicated" and enabled is not True:
        return reply(1, msg="Dedicated-server backups cannot be disabled."), 409
    Config.set_config("backup_enabled", enabled)
    return reply(0, SaveManager().session_summary())


@save_blueprint.route("/passive_skills", methods=["GET"])
@jwt_required()
def get_passive_skills():
    passives_raw = DataProvider.get_sorted_passives()
    passive_dict = {}
    passive_arr = []
    for passive in passives_raw:
        data = {
            "InternalName": passive["InternalName"],
            "I18n": DataProvider.get_passive_i18n_map(passive["InternalName"])
            or {
                "en": {"Name": passive["InternalName"], "Description": ""},
                "zh-CN": {"Name": passive["InternalName"], "Description": ""},
            },
            "Rating": passive["Rating"],
            "IsMutationExclusive": DataProvider.is_mutation_exclusive_passive(
                passive["InternalName"]
            ),
        }
        passive_dict[passive["InternalName"]] = data
        passive_arr.append(data)

    return reply(0, {"dict": passive_dict, "arr": passive_arr})


@save_blueprint.route("/active_skills", methods=["GET"])
@jwt_required()
def get_active_skills():
    attacks_raw = DataProvider.get_sorted_attacks()
    atk_dict = {}
    atk_arr = []
    for attack in attacks_raw:
        # if attack.get("Invalid", None):
        #     continue
        data = {
            "InternalName": attack["InternalName"],
            # "I18n": f'[{displayElement(attack["Element"])}] ' \
            #         f'{"🍐" if DataProvider.has_skill_fruit(attack["InternalName"]) else ""}' \
            #         f'{"✨"if DataProvider.is_unique_attacks(attack["InternalName"]) else ""}' \
            #         f'{DataProvider.get_attack_i18n(attack["InternalName"]) or attack["InternalName"]}',
            "I18n": DataProvider.get_attack_i18n_map(attack["InternalName"])
            or {
                "en": {"Name": attack["InternalName"], "Description": ""},
                "zh-CN": {"Name": attack["InternalName"], "Description": ""},
            },
            "HasSkillFruit": DataProvider.has_skill_fruit(attack["InternalName"]),
            "IsUniqueSkill": DataProvider.is_unique_attacks(attack["InternalName"]),
            "Power": attack["Power"],
            "Element": attack["Element"],
            "CT": attack["CT"],
            "Invalid": attack.get("Invalid", False),
        }
        atk_dict[attack["InternalName"]] = data
        atk_arr.append(data)
    return reply(0, {"dict": atk_dict, "arr": atk_arr})


@save_blueprint.route("/i18n", methods=["PATCH"])
# @jwt_required()
def update_i18n():
    i18n_code = request.json.get("I18n", None)
    if DataProvider.is_valid_i18n(i18n_code):
        Config.set_config("i18n", i18n_code)
        return reply(0)
    LOGGER.warning(
        f"I18n code {i18n_code} not available. Select from {DataProvider.get_i18n_options()}"
    )
    return reply(1, None, f"I18n code {i18n_code} not available.")


@save_blueprint.route("/pal_data", methods=["GET"])
@jwt_required()
def get_pal_data():
    pals_raw = DataProvider.get_sorted_pals()
    pal_dict = {}
    pal_arr = []
    for pal in pals_raw:
        iname = pal["InternalName"]
        if not DataProvider.is_editable_species(iname):
            continue
        data = {
            "InternalName": iname,
            "Elements": pal["Elements"],
            "Invalid": pal.get("Invalid", False),
            "Suitabilities": DataProvider.get_pal_suitabilities(iname),
            "I18n": DataProvider.get_pal_i18n_map(iname)
            or {"en": iname, "zh-CN": iname},
            "SortingKey": DataProvider.get_pal_sorting_key(iname),
            "IsHuman": DataProvider.is_pal_human(iname) or False,
            "IconAccessKey": iname if not DataProvider.is_pal_human(iname) or DataProvider.has_human_icon(iname) else "Human",
        }
        pal_dict[iname] = data
        pal_arr.append(data)
    return reply(0, {"dict": pal_dict, "arr": pal_arr})


@save_blueprint.route("/tech_data", methods=["GET"])
@jwt_required()
def get_tech_data():
    tech_data = DataProvider.get_tech_data()
    tech_lv_dict: dict[str, list] = {}
    for tech in tech_data:
        lv = DataProvider.get_tech_lv(tech)
        lv_arr = tech_lv_dict.get(lv, [])
        localized = DataProvider.get_tech_i18n(tech)
        data = {
            "InternalName": tech,
            "I18n": localized.get("Name", tech) if isinstance(localized, dict) else (localized or tech),
            "BossTechnology": DataProvider.is_boss_tech(tech),
            "Level": lv,
            "IconAccessKey": tech,
        }
        lv_arr.append(data)
        tech_lv_dict[lv] = lv_arr

    return reply(0, {"techLvDict": tech_lv_dict})


@save_blueprint.route("/path", methods=["GET"])
@jwt_required()
def get_path():
    candidates: list[Path] = []
    if isinstance(Config.path, str) and Config.path.strip():
        candidates.append(Path(Config.path))
    candidates.append(
        Path(os.environ.get("LOCALAPPDATA", "/")) / "Pal" / "Saved" / "SaveGames"
    )
    candidates.append(PROGRAM_PATH)

    last_error: Exception | None = None
    seen: set[str] = set()
    for current_path in candidates:
        key = str(current_path)
        if key in seen:
            continue
        seen.add(key)
        try:
            return _open_path_context(current_path)
        except Exception as exc:
            last_error = exc

    return _path_error_response(last_error or FileNotFoundError())


@save_blueprint.route("/path", methods=["POST"])
@jwt_required()
def update_path():
    payload = request.get_json(silent=True) or {}
    raw_path = payload.get("path")
    try:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("Path is required.")
        path = Path(raw_path.strip())
        if not path.is_absolute():
            raise ValueError("Path must be absolute.")
        return _open_path_context(path)
    except Exception as exc:
        return _path_error_response(exc)


@save_blueprint.route("/path", methods=["PATCH"])
@jwt_required()
def path_back():
    try:
        current_path = (
            Path(Config.path)
            if isinstance(Config.path, str) and Config.path.strip()
            else PROGRAM_PATH
        )
        return _open_path_context(current_path.parent)
    except Exception as exc:
        return _path_error_response(exc)

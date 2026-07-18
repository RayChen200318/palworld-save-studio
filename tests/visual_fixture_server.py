"""Local-only API fixture used for deterministic visual regression screenshots."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/palworld_save_studio/assets"
DATA = ASSETS / "data"
app = Flask(__name__)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


PALS = load("pal_data.json")
HUMANS = load("human_data.json")
PASSIVES = load("pal_passives.json")
ATTACKS = load("pal_attacks.json")
TECH = load("tech_data.json")
PLAYERS = [
    {"PlayerUId": "player-ray", "InstanceId": "instance-ray", "NickName": "Ray", "Level": 80, "HasViewingCage": True, "OtomoCharacterContainerId": "party-ray", "PalStorageContainerId": "palbox-ray", "TechnologyPoint": 42, "BossTechnologyPoint": 7, "PalCount": 96},
    {"PlayerUId": "player-mia", "InstanceId": "instance-mia", "NickName": "Mia", "Level": 62, "HasViewingCage": True, "OtomoCharacterContainerId": "party-mia", "PalStorageContainerId": "palbox-mia", "TechnologyPoint": 18, "BossTechnologyPoint": 3, "PalCount": 71},
    {"PlayerUId": "player-kai", "InstanceId": "instance-kai", "NickName": "Kai", "Level": 45, "HasViewingCage": False, "OtomoCharacterContainerId": "party-kai", "PalStorageContainerId": "palbox-kai", "TechnologyPoint": 9, "BossTechnologyPoint": 1, "PalCount": 38},
]
SPECIES = ["WorldTreeDragon", "KingWhale", "CactusDoll", "CloverFairy", "SamuraiDog", "FlowerPrince", "GrassMinotaur_Ice", "WhiteDeer_Dark", "DomeArmorDragon"]
HUMAN_SPECIES = ["Hunter_Rifle", "Hunter_Handgun", "Police_Rifle", "Male_Trader01"]
revision = 0


def ok(data=None):
    return jsonify({"status": 0, "data": data, "msg": None})


def localized(record):
    value = record.get("I18n", {}).get("zh-CN") or record.get("I18n", {}).get("en") or record["InternalName"]
    return value.get("Name", record["InternalName"]) if isinstance(value, dict) else value


def pal_summary(index: int):
    is_human = index % 11 == 10
    key = (HUMAN_SPECIES if is_human else SPECIES)[index % (len(HUMAN_SPECIES) if is_human else len(SPECIES))]
    record = (HUMANS if is_human else PALS)[key]
    owner = PLAYERS[index % len(PLAYERS)]
    locations = ["palbox", "base", "party", "outside"]
    location = locations[index % len(locations)]
    flags = ["outside-container"] if location == "outside" else (["boss"] if index % 9 == 0 else [])
    return {
        "InstanceId": f"pal-{index:04d}", "CharacterID": key, "SpeciesKey": key,
        "SpeciesName": localized(record), "NickName": "星尘" if index % 7 == 0 else "",
        "IconAccessKey": key if not is_human or record.get("HasIcon") else "Human",
        "PalDeckId": str(record.get("SortingKey", {}).get("paldeck", "")), "Level": 1 + index % 80,
        "Gender": None if is_human else ("EPalGenderType::Female" if index % 2 else "EPalGenderType::Male"),
        "OwnerPlayerUId": owner["PlayerUId"], "OwnerName": owner["NickName"],
        "ObjectType": "human" if is_human else "pal", "Location": location,
        "Elements": record.get("Elements", []), "StateFlags": flags, "IsAnomalous": bool(flags),
    }


PAL_ITEMS = [pal_summary(index) for index in range(240)]


def pal_detail(item):
    return item | {
        "group_id": "fixture-group", "ContainerId": f"container-{item['Location']}", "SlotIndex": 4,
        "DataAccessKey": item["SpeciesKey"], "DisplayName": item["SpeciesName"], "FriendshipLevel": 8,
        "HasBaseVariant": True, "HasBossVariant": not item["ObjectType"] == "human", "HasTowerVariant": item["SpeciesKey"] == "WorldTreeDragon",
        "HasWorkerSick": False, "IsFaintedPal": False, "Is_Unref_Pal": item["Location"] == "outside", "in_owner_palbox": item["Location"] in {"party", "palbox"},
        "IsHuman": item["ObjectType"] == "human", "IsBOSS": "boss" in item["StateFlags"], "IsRarePal": False, "IsTower": False,
        "IsRAID": False, "IsPREDATOR": False, "IsOilrig": False, "IsExpeditionPal": False, "IsAwakening": True,
        "ComputedMaxHP": 12480, "ComputedAttack": 918, "ComputedDefense": 742, "ComputedCraftSpeed": 126,
        "Rank": 5, "Rank_HP": 12, "Rank_Attack": 15, "Rank_Defence": 10, "Rank_CraftSpeed": 8,
        "Talent_HP": 96, "Talent_Melee": 82, "Talent_Shot": 100, "Talent_Defense": 91,
        "PassiveSkillList": ["Legend", "WorldTree_ATK", "WorldTree_DEF", "CraftSpeed_up3"],
        "EquipWaza": ["EPalWazaID::DragonCanon", "EPalWazaID::DarkWave", "EPalWazaID::AirCanon"],
        "MasteredWaza": ["EPalWazaID::DragonCanon", "EPalWazaID::DarkWave", "EPalWazaID::AirCanon", "EPalWazaID::WindCutter"],
        "Suitabilities": {"EPalWorkSuitability::Handcraft": 4, "EPalWorkSuitability::Mining": 3, "EPalWorkSuitability::Transport": 4},
    }


def session():
    return {"Path": r"C:\Users\Ray\AppData\Local\Pal\Saved\SaveGames\7656119\A62F18C9", "Loaded": True, "DirtyRevision": revision, "Dirty": revision > 0,
            "Statistics": {"Players": 3, "Pals": 218, "Humans": 22, "Anomalies": 60, "Objects": 240},
            "BackupEnabled": True, "BackupPath": r"C:\Fixture\Palworld-Save-Studio-Backup", "LastCommit": None}


@app.route("/api/save/fetch_config")
def config(): return ok({"I18n": "zh-CN", "I18nList": {"zh-CN": "简体中文", "en": "English"}, "Path": session()["Path"], "HasPassword": False, "VERSION": "0.2.0-beta.1", "IsOfficialBuild": False, "BackupEnabled": True})


@app.route("/api/auth/login", methods=["POST"])
def login(): return ok({"access_token": "visual-fixture"})


@app.route("/api/save/session")
def current_session(): return ok(session())


@app.route("/api/save/load", methods=["POST"])
def load_save(): return ok(session())


@app.route("/api/save/discard", methods=["POST"])
def discard():
    global revision
    revision = 0
    return ok(session())


@app.route("/api/save/commit", methods=["POST"])
def commit():
    global revision
    revision = 0
    return ok({"Commit": {"Verified": True, "FilesWritten": 4, "BackupPath": None, "Revision": 0}, "Session": session()})


@app.route("/api/save/settings", methods=["PATCH"])
def settings():
    data = session()
    data["BackupEnabled"] = bool(request.json.get("BackupEnabled"))
    return ok(data)


@app.route("/api/save/update")
def update_status():
    return ok({"CurrentVersion": "0.2.0-beta.1", "LatestVersion": None, "UpdateAvailable": False, "ReleaseUrl": None})


@app.route("/api/save/i18n", methods=["PATCH"])
def i18n(): return ok()


@app.route("/api/save/path", methods=["GET", "POST", "PATCH"])
def path(): return ok({"currentPath": session()["Path"], "children": {}, "isPalDir": True})


@app.route("/api/save/pal_data")
def pal_catalog():
    records = []
    for key in [*SPECIES, *HUMAN_SPECIES]:
        record = (HUMANS if key in HUMANS else PALS)[key]
        records.append({"InternalName": key, "Elements": record.get("Elements", []), "Invalid": False, "Suitabilities": record.get("Suitabilities", {}), "I18n": localized(record), "SortingKey": record.get("SortingKey", {}).get("paldeck", ""), "IsHuman": bool(record.get("Human")), "IconAccessKey": key if not record.get("Human") or record.get("HasIcon") else "Human"})
    return ok({"dict": {item["InternalName"]: item for item in records}, "arr": records})


@app.route("/api/save/passive_skills")
def passive_catalog():
    records = [{"InternalName": key, "I18n": [localized(value), value.get("I18n", {}).get("zh-CN", {}).get("Description", "")], "Rating": value.get("Rating", 0)} for key, value in list(PASSIVES.items())[:60]]
    return ok({"dict": {item["InternalName"]: item for item in records}, "arr": records})


@app.route("/api/save/active_skills")
def active_catalog():
    records = [{"InternalName": key, "I18n": [localized(value), ""], "HasSkillFruit": bool(value.get("SkillFruit")), "IsUniqueSkill": bool(value.get("UniqueSkill")), "Power": value.get("Power", 0), "Element": value.get("Element", ""), "CT": value.get("CT", 0), "Invalid": False} for key, value in list(ATTACKS.items())[:100]]
    return ok({"dict": {item["InternalName"]: item for item in records}, "arr": records})


@app.route("/api/save/tech_data")
def technology_catalog():
    grouped = {}
    for key, value in list(TECH.items())[:160]:
        level = value.get("Level", 0)
        grouped.setdefault(str(level), []).append({"InternalName": key, "I18n": localized(value), "BossTechnology": bool(value.get("BossTechnology")), "Level": level, "IconAccessKey": key})
    return ok({"techLvDict": grouped})


@app.route("/api/pal/list")
def list_pals(): return ok(PAL_ITEMS)


@app.route("/api/pal/<instance_id>", methods=["GET", "PATCH", "DELETE"])
def one_pal(instance_id):
    global revision
    item = next((pal for pal in PAL_ITEMS if pal["InstanceId"] == instance_id), PAL_ITEMS[0])
    if request.method == "DELETE":
        revision += 1
        return ok({"DirtyRevision": revision})
    detail = pal_detail(item)
    if request.method == "PATCH":
        detail.update(request.json.get("changes", {}))
        revision += 1
        return ok({"Pal": detail, "DirtyRevision": revision})
    return ok(detail)


@app.route("/api/pal", methods=["POST"])
def create_pal():
    global revision
    revision += 1
    item = pal_summary(241) | {"InstanceId": str(uuid4()), "CharacterID": request.json["CharacterID"], "SpeciesKey": request.json["CharacterID"]}
    return ok({"Pal": pal_detail(item), "DirtyRevision": revision})


@app.route("/api/pal/<instance_id>/duplicate", methods=["POST"])
def duplicate(instance_id):
    global revision
    revision += 1
    item = pal_detail(PAL_ITEMS[0]) | {"InstanceId": str(uuid4())}
    return ok({"Pal": item, "DirtyRevision": revision})


@app.route("/api/pal/<instance_id>/retrieve", methods=["POST"])
def retrieve(instance_id):
    global revision
    revision += 1
    return ok({"Pal": pal_detail(PAL_ITEMS[0]) | {"InstanceId": instance_id, "Location": "palbox"}, "DirtyRevision": revision})


@app.route("/api/pal/heal-all", methods=["POST"])
def heal():
    global revision
    revision += 1
    return ok({"Healed": len(PAL_ITEMS), "DirtyRevision": revision})


@app.route("/api/pal/<instance_id>/raw")
def raw(instance_id): return ok({"Json": json.dumps(pal_detail(PAL_ITEMS[0]), ensure_ascii=False, indent=2)})


@app.route("/api/player")
def players(): return ok(PLAYERS)


@app.route("/api/player/<player_id>", methods=["GET", "PATCH"])
def player(player_id):
    global revision
    value = next(item for item in PLAYERS if item["PlayerUId"] == player_id) | {"UnlockedRecipeTechnologyNames": list(TECH)[:90]}
    if request.method == "PATCH":
        value.update(request.json.get("changes", {}))
        revision += 1
        return ok({"Player": value, "DirtyRevision": revision})
    return ok(value)


@app.route("/api/player/<player_id>/technology/<technology_id>", methods=["PATCH"])
def toggle_technology(player_id, technology_id):
    global revision
    revision += 1
    return ok({"Technology": technology_id, "Enabled": bool(request.json.get("Enabled")), "DirtyRevision": revision})


@app.route("/api/player/<player_id>/technology/unlock-all", methods=["POST"])
def unlock_all(player_id):
    global revision
    revision += 1
    value = next(item for item in PLAYERS if item["PlayerUId"] == player_id) | {"UnlockedRecipeTechnologyNames": list(TECH)}
    return ok({"Player": value, "DirtyRevision": revision})


@app.route("/image/<icon_type>/<path:filename>")
def image(icon_type, filename):
    path = ASSETS / "icons" / icon_type
    target = path / f"{filename}.png"
    if not target.is_file() and icon_type == "pals": target = ASSETS / "icons/pals/unknown.png"
    if not target.is_file(): return "", 404
    return send_from_directory(target.parent, target.name)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    dist = ROOT / "frontend/dist"
    target = dist / path
    if path and target.is_file():
        return send_from_directory(dist, path)
    return send_from_directory(dist, "index.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=58080, debug=False, use_reloader=False)

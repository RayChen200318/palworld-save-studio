import copy
from pathlib import Path
import tempfile
import traceback
from typing import Any, Optional
import uuid

from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.archive import FArchiveReader, FArchiveWriter, UUID
from palworld_save_tools.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from palworld_save_tools.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS

from palworld_save_studio.core.basecamp_data import BaseCampData

from palworld_save_studio.core.container_data import ContainerData

from palworld_save_studio.core.pal_objects import PalObjects, UUID2HexStr, toUUID
from palworld_save_studio.core.player_entity import PlayerEntity
from palworld_save_studio.core.pal_entity import PalEntity
from palworld_save_studio.utils import LOGGER, alphanumeric_key
from palworld_save_studio.core.group_data import GroupData
from palworld_save_studio.config import Config, VERSION
from palworld_save_studio.core.save_transaction import (
    BACKUP_FOLDER_NAME,
    SaveTransactionError,
    capture_source_manifest,
    core_save_paths,
    replace_staged_files,
    source_manifest_matches,
)
from palworld_save_studio.core.item_inventory import ItemInventoryService
from palworld_save_studio.core.save_schema import (
    SaveSchemaError,
    validate_editable_schema,
)


def skip_decode(reader: FArchiveReader, type_name: str, size: int, path: str):
    if type_name == "ArrayProperty":
        array_type = reader.fstring()
        value = {
            "skip_type": type_name,
            "array_type": array_type,
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    elif type_name == "MapProperty":
        key_type = reader.fstring()
        value_type = reader.fstring()
        _id = reader.optional_guid()
        value = {
            "skip_type": type_name,
            "key_type": key_type,
            "value_type": value_type,
            "id": _id,
            "value": reader.read(size),
        }
    elif type_name == "StructProperty":
        value = {
            "skip_type": type_name,
            "struct_type": reader.fstring(),
            "struct_id": reader.guid(),
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    else:
        raise Exception(
            f"Expected ArrayProperty or MapProperty or StructProperty, got {type_name} in {path}"
        )
    return value


def skip_encode(writer: FArchiveWriter, property_type: str, properties: dict) -> int:
    if "skip_type" not in properties:
        if properties["custom_type"] in PALWORLD_CUSTOM_PROPERTIES is not None:
            return PALWORLD_CUSTOM_PROPERTIES[properties["custom_type"]][1](
                writer, property_type, properties
            )
        else:
            # Never be run to here
            return writer.property_inner(writer, property_type, properties)
    if property_type == "ArrayProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["array_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "MapProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["key_type"])
        writer.fstring(properties["value_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "StructProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["struct_type"])
        writer.guid(properties["struct_id"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    else:
        raise Exception(
            f"Expected ArrayProperty or MapProperty or StructProperty, got {property_type}"
        )


MAIN_SKIP_PROPERTIES = copy.deepcopy(PALWORLD_CUSTOM_PROPERTIES)
MAIN_SKIP_PROPERTIES[".worldSaveData.MapObjectSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.FoliageGridSaveDataMap"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.MapObjectSpawnerInStageSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.WorkSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.DungeonSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.EnemyCampSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.CharacterParameterStorageSaveData"] = (skip_decode, skip_encode)

MAIN_SKIP_PROPERTIES[".worldSaveData.InvaderSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.DungeonPointMarkerSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.GameTimeSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.FixedWeaponDestroySaveData"] = (skip_decode, skip_encode)

MAIN_SKIP_PROPERTIES[".worldSaveData.OilrigSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.SupplySaveData"] = (skip_decode, skip_encode)

MAIN_SKIP_PROPERTIES[".worldSaveData.RandomizerSaveData"] = (skip_decode, skip_encode)
MAIN_SKIP_PROPERTIES[".worldSaveData.GuildExtraSaveDataMap"] = (skip_decode, skip_encode)


PLAYER_SKIP_PROPERTIES = copy.deepcopy(PALWORLD_CUSTOM_PROPERTIES)
PLAYER_SKIP_PROPERTIES[".SaveData.PlayerCharacterMakeData"] = (skip_decode, skip_encode)
PLAYER_SKIP_PROPERTIES[".SaveData.LastTransform"] = (skip_decode, skip_encode)
PLAYER_SKIP_PROPERTIES[".SaveData.inventoryInfo"] = (skip_decode, skip_encode)
# PLAYER_SKIP_PROPERTIES[".SaveData.RecordData"] = (skip_decode, skip_encode)

class SaveManager:
    # Although these are class attrs, SaveManager itself is singleton so it should be fine?
    _instance = None
    _file_path: Optional[Path]
    _raw_gvas: Optional[bytes]
    _save_type: Optional[int]

    gvas_file: Optional[GvasFile]
    _entities_list: Optional[list[dict]]

    player_mapping: Optional[dict[str, PlayerEntity]]
    baseworker_mapping: Optional[dict[str, PalEntity]]
    _dangling_pals: Optional[dict[str, PalEntity]]

    container_data: Optional[ContainerData]
    group_data: Optional[GroupData]
    camp_data: Optional[BaseCampData]
    item_inventory: Optional[ItemInventoryService]

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._file_path = None
            self._raw_gvas = None
            self._save_type = None
            self.gvas_file = None
            self._entities_list = None
            self.player_mapping = {}
            self.baseworker_mapping = {}
            self._dangling_pals = {}
            self.container_data = None
            self.group_data = None
            self.camp_data = None
            self.item_inventory = None
            self._loaded = False
            self._dirty_revision = 0
            self._last_commit: dict[str, Any] | None = None
            self._save_kind = "local"
            self._source_manifest: dict[str, dict[str, Any]] = {}
            self._source_verified = False

    @staticmethod
    def _validate_save_root(path: Path, save_kind: str) -> None:
        if save_kind not in {"local", "dedicated"}:
            raise SaveTransactionError("SaveKind must be 'local' or 'dedicated'.")
        if save_kind != "dedicated":
            return
        if (path / "Level.sav").is_file() and (path / "Players").is_dir():
            return

        nested_worlds: list[Path] = []
        if path.is_dir():
            for child in path.iterdir():
                if not child.is_dir():
                    continue
                if (child / "Level.sav").is_file() and (child / "Players").is_dir():
                    nested_worlds.append(child)
                    continue
                for grandchild in child.iterdir():
                    if (
                        grandchild.is_dir()
                        and (grandchild / "Level.sav").is_file()
                        and (grandchild / "Players").is_dir()
                    ):
                        nested_worlds.append(grandchild)
        if len(nested_worlds) == 1:
            raise SaveTransactionError(
                "Select the WorldID folder directly, not its parent. The correct folder is: "
                f"{nested_worlds[0]}"
            )
        raise SaveTransactionError(
            "A dedicated-server WorldID folder must directly contain Level.sav and Players. "
            "Example: <WorldID>/Level.sav and <WorldID>/Players/."
        )

    def open(
        self,
        file_path: str,
        *,
        save_kind: str | None = None,
        reset_session: bool = True,
    ) -> Optional[GvasFile]:
        selected_kind = save_kind or self._save_kind
        self._file_path = Path(file_path).resolve()
        self._validate_save_root(self._file_path, selected_kind)
        self._save_kind = selected_kind

        level_sav_path = self._file_path / "Level.sav"

        if not level_sav_path.exists():
            LOGGER.error(f"Save file does not exist: {level_sav_path}.")
            return None

        LOGGER.info(f"Opening {level_sav_path}")
        with level_sav_path.open("rb") as file:
            data = file.read()

            try:
                LOGGER.info("Decompressing sav")
                self._raw_gvas, self._save_type = decompress_sav_to_gvas(
                    data, debug=Config.debug
                )

                # LOGGER.info("Compressing Main GVAS file")
                # sav_data = compress_gvas_to_sav(
                #     self._raw_gvas,
                #     # self._save_type,
                #     0x32,
                #     True
                # )

                # with level_sav_path.open("wb") as file:
                #     file.write(sav_data)

                # return
            except Exception as e:
                LOGGER.error(f"Caught Exception: palworld_save_tools::palsav::decompress_sav_to_gvas: {e}")
                return None

            LOGGER.info("Reading GVAS file")
            self.gvas_file = GvasFile.read(
                self._raw_gvas, PALWORLD_TYPE_HINTS, MAIN_SKIP_PROPERTIES
            )

            PalObjects.TIME = PalObjects.get_BaseType(self.gvas_file.properties.get("Timestamp")) or PalObjects.TIME

            try:
                self.group_data = GroupData(self.gvas_file)
            except Exception as e:
                LOGGER.error(f"Error parsing group data: {e}")
                return None

            try:
                self.camp_data = BaseCampData(self.gvas_file)
            except Exception as e:
                LOGGER.error(f"Error parsing base camp data: {e}")
                return None

            try:
                self.container_data = ContainerData(self.gvas_file)
            except Exception as e:
                LOGGER.error(f"Error parsing container data: {e}")
                return None

            try:
                self._entities_list = self.gvas_file.properties["worldSaveData"]["value"]["CharacterSaveParameterMap"]["value"]
            except Exception as e:
                LOGGER.error(f"Unable to retrieve pal data: {e}")
                return None

            self._load_entities()

            try:
                self.item_inventory = ItemInventoryService(self)
            except Exception as e:
                LOGGER.error(f"Error parsing player item inventories: {e}")
                return None

            LOGGER.info("Done")
        self._loaded = True
        self._source_manifest = capture_source_manifest(self._file_path)
        self._source_verified = True
        if reset_session:
            self._dirty_revision = 0
            self._last_commit = None
        return self.gvas_file

    def save(self, file_path: str | None = None) -> bool:
        """CLI save entry point; the GUI writes only to the loaded path."""
        if file_path and self._file_path and Path(file_path).resolve() != self._file_path:
            LOGGER.error("Save As is not supported by Palworld Save Studio.")
            return False
        return bool(self.commit().get("Verified"))

    def _serialize_to(self, output_path: Path) -> list[Path]:
        if self.gvas_file is None or self._save_type is None:
            raise SaveTransactionError("No loaded save is available.")

        output_path.mkdir(parents=True, exist_ok=True)
        relative_paths: list[Path] = []
        for player in self.player_mapping.values():
            if not self.save_player_sav(player, output_path):
                raise SaveTransactionError(f"Unable to serialize player {player.PlayerUId}.")
            relative_paths.append(Path("Players") / f"{UUID2HexStr(player.PlayerUId)}.sav")

        level_path = output_path / "Level.sav"
        gvas_file = copy.deepcopy(self.gvas_file)
        sav_data = compress_gvas_to_sav(
            gvas_file.write(MAIN_SKIP_PROPERTIES),
            self._save_type,
            debug=Config.debug,
        )
        level_path.write_bytes(sav_data)
        return [Path("Level.sav"), *relative_paths]

    def _validate_staged_files(self, staged_root: Path, paths: list[Path]) -> None:
        for relative_path in paths:
            raw_gvas, _ = decompress_sav_to_gvas(
                (staged_root / relative_path).read_bytes(), debug=Config.debug
            )
            properties = (
                MAIN_SKIP_PROPERTIES
                if relative_path == Path("Level.sav")
                else PLAYER_SKIP_PROPERTIES
            )
            GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, properties)

    def _capture_runtime_state(self) -> dict[str, Any]:
        return {
            key: getattr(self, key)
            for key in (
                "_file_path",
                "_raw_gvas",
                "_save_type",
                "gvas_file",
                "_entities_list",
                "player_mapping",
                "baseworker_mapping",
                "_dangling_pals",
                "container_data",
                "group_data",
                "camp_data",
                "item_inventory",
                "_loaded",
                "_dirty_revision",
                "_last_commit",
                "_save_kind",
                "_source_manifest",
                "_source_verified",
            )
        }

    def _restore_runtime_state(self, state: dict[str, Any]) -> None:
        for key, value in state.items():
            setattr(self, key, value)

    def _semantic_snapshot(self) -> dict[str, Any]:
        players = []
        for player in sorted(self.get_players(), key=lambda item: str(item.PlayerUId)):
            players.append(
                {
                    "id": str(player.PlayerUId),
                    "nickname": player.NickName or "",
                    "level": player.Level or 1,
                    "exp": player.Exp,
                    "unused_status_points": player.UnusedStatusPoint,
                    "technology_points": player.TechnologyPoint or 0,
                    "boss_technology_points": player.bossTechnologyPoint or 0,
                    "technology": sorted(player.UnlockedRecipeTechnologyNames or []),
                }
            )

        pals = []
        for context in self.get_all_pal_contexts():
            pal = context["pal"]
            pals.append(
                {
                    "id": str(pal.InstanceId),
                    "character_id": pal.CharacterID,
                    "nickname": pal.NickName or "",
                    "gender": pal.Gender.value if pal.Gender else None,
                    "level": pal.Level or 1,
                    "exp": pal.Exp,
                    "friendship": pal.FriendshipLevel or 0,
                    "rank": pal.Rank or 1,
                    "soul": [
                        pal.Rank_HP or 0,
                        pal.Rank_Attack or 0,
                        pal.Rank_Defence or 0,
                        pal.Rank_CraftSpeed or 0,
                    ],
                    "iv": [
                        pal.Talent_HP or 0,
                        pal.Talent_Melee or 0,
                        pal.Talent_Shot or 0,
                        pal.Talent_Defense or 0,
                    ],
                    "passives": list(pal.PassiveSkillList or []),
                    "mastered": list(pal.MasteredWaza or []),
                    "equipped": list(pal.EquipWaza or []),
                    "work": dict(sorted((pal.WorkSuitabilities or {}).items())),
                    "flags": [
                        bool(pal.IsBOSS),
                        bool(pal.IsRarePal),
                        bool(pal.IsTower),
                        bool(pal.IsAwakening),
                    ],
                    "health": {
                        "hp": pal.Hp,
                        "sanity": pal.SanityValue,
                        "stomach": pal.FullStomach,
                        "worker_sick": pal.WorkerSick,
                        "hunger": pal.HungerType,
                        "revive_timer": pal.PalReviveTimer,
                        "physical_health": pal.PhysicalHealth,
                    },
                    "container": str(pal.ContainerId) if pal.ContainerId else None,
                    "slot": pal.SlotIndex,
                    "owner": str(pal.OwnerPlayerUId) if pal.OwnerPlayerUId else None,
                }
            )
        pals.sort(key=lambda item: item["id"])
        return {
            "players": players,
            "pals": pals,
            "items": self.item_inventory.semantic_snapshot() if self.item_inventory else None,
        }

    @staticmethod
    def _raw_save_bytes(path: Path) -> bytes:
        raw_gvas, _ = decompress_sav_to_gvas(path.read_bytes(), debug=Config.debug)
        return raw_gvas

    def _partition_staged_files(
        self, staged_root: Path, paths: list[Path]
    ) -> tuple[list[Path], list[Path]]:
        if self._file_path is None:
            raise SaveTransactionError("No loaded save is available.")
        changed: list[Path] = []
        skipped: list[Path] = []
        for relative_path in paths:
            source = self._file_path / relative_path
            staged = staged_root / relative_path
            if source.is_file() and self._raw_save_bytes(source) == self._raw_save_bytes(staged):
                skipped.append(relative_path)
            else:
                changed.append(relative_path)
        return changed, skipped

    def _reported_skipped_paths(
        self, changed: list[Path], serialized_skipped: list[Path]
    ) -> list[Path]:
        if self._file_path is None or self._save_kind != "dedicated":
            return list(serialized_skipped)
        changed_set = set(changed)
        return [
            relative_path
            for relative_path in core_save_paths(self._file_path)
            if relative_path not in changed_set
        ]

    def _validate_before_commit(self) -> None:
        try:
            validate_editable_schema(self)
        except (SaveSchemaError, ValueError, KeyError, TypeError) as exc:
            raise SaveTransactionError(f"Save structure validation failed: {exc}") from exc

    def _prepare_staged_commit(
        self, transaction_root: Path
    ) -> tuple[Path, list[Path], list[Path]]:
        staged_root = transaction_root / "staged"
        paths = self._serialize_to(staged_root)
        self._validate_staged_files(staged_root, paths)
        changed, skipped = self._partition_staged_files(staged_root, paths)
        return staged_root, changed, skipped

    def _verify_source_unchanged(self) -> None:
        if self._file_path is None:
            raise SaveTransactionError("No save is loaded.")
        self._source_verified = source_manifest_matches(
            self._file_path, self._source_manifest
        )
        if not self._source_verified:
            raise SaveTransactionError(
                "The save changed on disk after it was opened. No files were written; reload the save before editing again."
            )

    def commit_preview(self) -> dict[str, Any]:
        if not self._loaded or self._file_path is None:
            raise SaveTransactionError("No save is loaded.")
        self._verify_source_unchanged()
        self._validate_before_commit()
        if self._dirty_revision == 0:
            return {
                "SourceVerified": True,
                "FilesChanged": [],
                "FilesSkipped": [],
                "BackupPath": str(self._file_path / BACKUP_FOLDER_NAME),
                "WorldId": self._file_path.name,
            }

        transaction_root = Path(
            tempfile.mkdtemp(
                prefix=".palworld-save-studio-preview-",
                dir=self._file_path.parent,
            )
        )
        try:
            _, changed, skipped = self._prepare_staged_commit(transaction_root)
            skipped = self._reported_skipped_paths(changed, skipped)
            return {
                "SourceVerified": True,
                "FilesChanged": [path.as_posix() for path in changed],
                "FilesSkipped": [path.as_posix() for path in skipped],
                "BackupPath": str(self._file_path / BACKUP_FOLDER_NAME),
                "WorldId": self._file_path.name,
            }
        finally:
            import shutil

            shutil.rmtree(transaction_root, ignore_errors=True)

    def commit(self, *, server_stopped_confirmed: bool = False) -> dict[str, Any]:
        if not self._loaded or self._file_path is None:
            raise SaveTransactionError("No save is loaded.")
        if not self._file_path.is_dir():
            raise SaveTransactionError(f"Loaded path is unavailable: {self._file_path}")
        if self._save_kind == "dedicated" and server_stopped_confirmed is not True:
            raise SaveTransactionError(
                "Confirm that PalServer is fully stopped before saving a dedicated-server world."
            )
        self._verify_source_unchanged()
        if self._dirty_revision == 0:
            return {
                "Verified": True,
                "FilesWritten": 0,
                "SourceVerified": self._source_verified,
                "FilesChanged": [],
                "FilesSkipped": [],
                "BackupPath": None,
                "Revision": 0,
            }

        self._validate_before_commit()
        intended_snapshot = self._semantic_snapshot()
        runtime_state = self._capture_runtime_state()
        transaction_root = Path(
            tempfile.mkdtemp(
                prefix=".palworld-save-studio-transaction-",
                dir=self._file_path.parent,
            )
        )
        try:
            staged_root, changed, skipped = self._prepare_staged_commit(
                transaction_root
            )
            skipped = self._reported_skipped_paths(changed, skipped)

            if not changed:
                backup_path = None
                if self._save_kind == "dedicated":
                    backup_result = replace_staged_files(
                        save_root=self._file_path,
                        staged_root=staged_root,
                        transaction_root=transaction_root,
                        relative_paths=(),
                        backup_enabled=True,
                        verify=lambda: True,
                        backup_paths=core_save_paths(self._file_path),
                        backup_metadata={
                            "StudioVersion": VERSION,
                            "SaveKind": self._save_kind,
                            "WorldId": self._file_path.name,
                        },
                        files_skipped=skipped,
                        pre_write_check=lambda: source_manifest_matches(
                            self._file_path, self._source_manifest
                        ),
                    )
                    backup_path = backup_result.backup_path
                self._dirty_revision = 0
                self._last_commit = {
                    "Verified": True,
                    "FilesWritten": 0,
                    "SourceVerified": True,
                    "FilesChanged": [],
                    "FilesSkipped": [path.as_posix() for path in skipped],
                    "BackupPath": backup_path,
                    "Revision": 0,
                }
                return dict(self._last_commit)

            def verify() -> bool:
                if not self.open(
                    str(self._file_path),
                    save_kind=self._save_kind,
                    reset_session=False,
                ):
                    return False
                self._validate_before_commit()
                return self._semantic_snapshot() == intended_snapshot

            backup_required = self._save_kind == "dedicated"
            result = replace_staged_files(
                save_root=self._file_path,
                staged_root=staged_root,
                transaction_root=transaction_root,
                relative_paths=changed,
                backup_enabled=backup_required or Config.backup_enabled,
                verify=verify,
                backup_paths=(
                    core_save_paths(self._file_path) if backup_required else changed
                ),
                backup_metadata={
                    "StudioVersion": VERSION,
                    "SaveKind": self._save_kind,
                    "WorldId": self._file_path.name,
                },
                files_skipped=skipped,
                pre_write_check=lambda: source_manifest_matches(
                    self._file_path, self._source_manifest
                ),
            )
        except Exception:
            self._restore_runtime_state(runtime_state)
            raise
        finally:
            import shutil

            shutil.rmtree(transaction_root, ignore_errors=True)

        self._dirty_revision = 0
        self._last_commit = {
            "Verified": result.verified,
            "FilesWritten": result.files_written,
            "SourceVerified": result.source_verified,
            "FilesChanged": list(result.files_changed),
            "FilesSkipped": list(result.files_skipped),
            "BackupPath": result.backup_path,
            "Revision": 0,
        }
        return dict(self._last_commit)

    def load_player_sav(self, player_uid: str | UUID) -> tuple[GvasFile, int]:
        player_path: Path = self._file_path / "Players" / f"{UUID2HexStr(player_uid)}.sav"
        LOGGER.info(f"Loading Player SAV: {player_path}")
        if not player_path.exists():
            LOGGER.error(f"Player SAV {str(player_path.absolute())} not exist")
            raise Exception(f"Player SAV {str(player_path.absolute())} not exist")
        with player_path.open("rb") as player_file:
            player_data = player_file.read()
        raw_gvas, save_type = decompress_sav_to_gvas(
            player_data, debug=Config.debug
        )
        player_gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, PLAYER_SKIP_PROPERTIES)
        return player_gvas_file, save_type


    def save_player_sav(self, player_entity: PlayerEntity, save_path: Optional[Path] = None) -> bool:
        if player_entity.PlayerGVAS is None:
            return False

        save_data_backup = copy.deepcopy(player_entity._player_save_data)
        new_palbox_backup = dict(player_entity._new_palbox)
        new_pal_flags = {
            key: pal.is_new_pal for key, pal in player_entity._new_palbox.items()
        }
        try:
            player_entity.save_new_pal_records()
            gvas_file, save_type = player_entity.PlayerGVAS
            player_gvas_file = copy.deepcopy(gvas_file)
        finally:
            player_entity._player_save_data.clear()
            player_entity._player_save_data.update(save_data_backup)
            player_entity._new_palbox.clear()
            player_entity._new_palbox.update(new_palbox_backup)
            for key, is_new in new_pal_flags.items():
                if key in player_entity._new_palbox:
                    player_entity._new_palbox[key].is_new_pal = is_new

        output_path = (save_path or self._file_path) / "Players"
        if not output_path.exists() and output_path.parent.exists():
            LOGGER.warning(f"Player path does not exist: {output_path}")
            output_path.mkdir(parents=True, exist_ok=True)
            LOGGER.info(f"Player path {output_path} created")

        player_path: Path = output_path / f"{UUID2HexStr(player_entity.PlayerUId)}.sav"

        LOGGER.info(f"Compressing Player {player_entity} GVAS file")
        sav_data = compress_gvas_to_sav(
            player_gvas_file.write(PLAYER_SKIP_PROPERTIES),
            save_type,
            debug=Config.debug,
        )

        LOGGER.info(f"Saving to {player_path}")
        with player_path.open("wb") as file:
            file.write(sav_data)
        LOGGER.info(f"Saved to {player_path}")
        return True

    def _load_entities(self):
        self.player_mapping = {}
        self._dangling_pals = {}
        self.baseworker_mapping = {}
        temp_player_pal_mapping: dict[str, dict[str, PalEntity]] = {}
        for entity in self._entities_list:
            entity_struct = entity["value"]["RawData"]["value"]["object"]["SaveParameter"]
            if entity_struct['struct_type'] != 'PalIndividualCharacterSaveParameter':
                LOGGER.warning(f"Non-player/pal data found in CharacterSaveParameterMap, skipping {entity}")
                continue

            entity_param: dict = entity_struct['value']
            try:
                if PalObjects.get_BaseType(entity_param.get("IsPlayer")):
                    uid_str = str(PalObjects.get_BaseType(entity["key"].get("PlayerUId")))
                    nickname = str(PalObjects.get_BaseType(entity_param.get("NickName")))
                    LOGGER.info(f"Players found: {nickname} - {uid_str}")
                    if uid_str in self.player_mapping:
                        LOGGER.error(f"Duplicated player found: \n\t{self.player_mapping[uid_str]}, skipping...")
                        continue

                    group_id = self.group_data.get_player_group_id(uid_str)

                    if group_id is None:
                        LOGGER.warning(f"Player {uid_str} has no guild id")
                        continue

                    player_gvas_file, player_save_type = self.load_player_sav(uid_str)

                    if uid_str in temp_player_pal_mapping:
                        player_entity = PlayerEntity(group_id, entity, temp_player_pal_mapping[uid_str], player_gvas_file, player_save_type)
                        del temp_player_pal_mapping[uid_str]
                    else:
                        player_entity = PlayerEntity(group_id, entity, dict(), player_gvas_file, player_save_type)

                    self.player_mapping[uid_str] = player_entity
                    LOGGER.info(f"Player Object Created: {player_entity}")
                else:
                    pal_entity = PalEntity(entity)
                    container_id, slot_idx = pal_entity.SlotId
                    group_id = pal_entity.group_id
                    # is_unref_pal = not self.group_data.get_group(group_id).has_pal(pal_entity.InstanceId)
                    pal_container = self.container_data.get_container(container_id)
                    is_unref_pal = (not pal_container) or (not pal_container.has_pal(pal_entity.InstanceId))
                    if is_unref_pal:
                        LOGGER.info(f"Likely Ghost Pal: {pal_entity}")
                    pal_entity.is_unreferenced_pal = is_unref_pal

                    owner = pal_entity.OwnerPlayerUId
                    if owner:
                        owner_str = str(owner)
                        if owner_str in self.player_mapping:
                            self.player_mapping[owner_str].add_pal(pal_entity)
                        else:
                            temp_player_pal_mapping.setdefault(owner_str, dict())[str(pal_entity.InstanceId)] = pal_entity
                        LOGGER.info(f"Found pal: {pal_entity}")

                    else:
                        if pal_entity.OldOwnerPlayerUIds:
                            self.baseworker_mapping[str(pal_entity.InstanceId)] = pal_entity
                            continue
                        self._dangling_pals[str(pal_entity.InstanceId)] = pal_entity
                        LOGGER.error(f"Found dangling pal object: {pal_entity}, skipping")
                        continue

            except Exception as e:
                LOGGER.error(f"Error occured while init'in object: {e}, skipping")
                continue


        for player in self.player_mapping.values():
            LOGGER.newline()
            LOGGER.info(f"{player}")
            sorted_palbox = player.get_sorted_pals()
            for pal in sorted_palbox:
                LOGGER.info(f"\t{pal}")

        LOGGER.newline()
        LOGGER.info("Pals possibly working at the base: ")
        for pal in self.get_working_pals():
            LOGGER.info(f"\t{pal}")

        LOGGER.newline()
        LOGGER.info("Dangling Pals (No OwnerID and OldOwnerID): ")
        for pal in self._dangling_pals.values():
            LOGGER.warning(f"\t{pal}")

        for uid_str in temp_player_pal_mapping:
            pal_list = temp_player_pal_mapping[uid_str]
            LOGGER.newline()
            LOGGER.warning(f"Found dangling pals owned by non-existing user {uid_str}")
            for pal in pal_list.values():
                self._dangling_pals[str(pal.InstanceId)] = pal
                LOGGER.warning(f"\t{pal}")

    def get_players(self) -> list[PlayerEntity]:
        return self.player_mapping.values()

    def get_player(self, guid: UUID | str) -> Optional[PlayerEntity]:
        if guid is None: return
        guid = str(guid)
        if guid in self.player_mapping:
            player = self.player_mapping[guid]
            return player
        # LOGGER.warning(f"Player {guid} not exist")

    def get_players_by_name(self, name: str) -> list[PlayerEntity]:
        return [player for player in self.get_players() if player.NickName == name]

    def get_working_pal(self, guid: UUID | str) -> Optional[PalEntity]:
        return self.baseworker_mapping.get(str(guid), None)

    def get_pal(self, guid: UUID | str) -> Optional[PalEntity]:
        guid = str(guid)
        if guid in self.baseworker_mapping:
            return self.baseworker_mapping[guid]
        if guid in self._dangling_pals:
            return self._dangling_pals[guid]
        for player in self.get_players():
            if pal := player.get_pal(guid, disable_warning=True):
                return pal

        LOGGER.warning(f"Can't find pal {guid}")

    def get_all_pal_contexts(self) -> list[dict[str, Any]]:
        contexts: dict[str, dict[str, Any]] = {}
        for player in self.get_players():
            for pal in player._palbox.values():
                instance_id = str(pal.InstanceId)
                if pal.ContainerId == player.OtomoCharacterContainerId:
                    location = "party"
                elif pal.ContainerId == player.PalStorageContainerId:
                    location = "palbox"
                else:
                    location = "outside"
                contexts[instance_id] = {
                    "pal": pal,
                    "owner": player,
                    "location": location,
                }

        for instance_id, pal in self.baseworker_mapping.items():
            owner = self.get_player(pal.LastOwnerPlayerUId or pal.OwnerPlayerUId)
            contexts[instance_id] = {
                "pal": pal,
                "owner": owner,
                "location": "base",
            }

        for instance_id, pal in self._dangling_pals.items():
            contexts.setdefault(
                instance_id,
                {
                    "pal": pal,
                    "owner": self.get_player(pal.LastOwnerPlayerUId or pal.OwnerPlayerUId),
                    "location": "outside",
                },
            )
        return list(contexts.values())

    def get_pal_context(self, guid: UUID | str) -> Optional[dict[str, Any]]:
        guid = str(guid)
        for context in self.get_all_pal_contexts():
            if str(context["pal"].InstanceId) == guid:
                return context

    def mark_dirty(self) -> int:
        if not self._loaded:
            raise RuntimeError("No save is loaded.")
        self._dirty_revision += 1
        return self._dirty_revision

    @property
    def has_draft(self) -> bool:
        return self._dirty_revision > 0

    def discard(self) -> bool:
        if not self._loaded or self._file_path is None:
            return False
        state = self._capture_runtime_state()
        try:
            if self.open(
                str(self._file_path),
                save_kind=self._save_kind,
                reset_session=True,
            ):
                return True
        except Exception:
            LOGGER.error(f"Failed discarding draft: {traceback.format_exc()}")
        self._restore_runtime_state(state)
        return False

    def session_summary(self) -> dict[str, Any]:
        contexts = self.get_all_pal_contexts() if self._loaded else []
        human_count = sum(bool(context["pal"].IsHuman) for context in contexts)
        pal_count = len(contexts) - human_count
        anomaly_count = sum(
            bool(
                context["pal"].is_unreferenced_pal
                or context["pal"].HasWorkerSick
                or context["pal"].IsFaintedPal
                or context["location"] == "outside"
            )
            for context in contexts
        )
        loaded_path = str(self._file_path) if self._file_path else Config.path
        backup_required = self._save_kind == "dedicated"
        return {
            "Path": loaded_path,
            "Loaded": self._loaded,
            "SaveKind": self._save_kind,
            "WorldId": self._file_path.name if self._file_path else None,
            "BackupRequired": backup_required,
            "SourceVerified": self._source_verified,
            "DirtyRevision": self._dirty_revision,
            "Dirty": self._dirty_revision > 0,
            "Statistics": {
                "Players": len(self.player_mapping or {}),
                "Pals": pal_count,
                "Humans": human_count,
                "Anomalies": anomaly_count,
                "Objects": len(contexts),
            },
            "BackupEnabled": backup_required or Config.backup_enabled,
            "BackupPath": (
                str(Path(loaded_path) / BACKUP_FOLDER_NAME) if loaded_path else None
            ),
            "LastCommit": self._last_commit,
        }

    def get_working_pals(self) -> list[PalEntity]:
        return sorted(self.baseworker_mapping.values(), key=lambda pal: (alphanumeric_key(pal.PalDeckID), pal.Level or 1))


    def move_pal(self, pal_id: UUID | str, target_container_ids: list[UUID | str]) -> bool:
        pal_entity = self.get_pal(pal_id)
        if not pal_entity: raise Exception("Pal Not Found")

        pal_container = None
        for id in target_container_ids:
            if container := self.container_data.get_container(id):
                if container.get_empty_slot() != -1:
                    pal_container = container
                    break

        if pal_container is None:
            LOGGER.info("No Empty Pal Slot")
            return False

        if pal_container.has_pal(pal_id):
            raise Exception("Pal already in the target container.")

        old_container = self.container_data.get_container(pal_entity.ContainerId)
        if old_container:
            old_container.del_pal(pal_id)

        if (slot_idx := pal_container.add_pal(pal_id)) == -1:
            return False

        pal_entity.SlotId = (pal_container.ID, slot_idx)
        return True

    def retrieve_pal(self, pal_id: UUID | str, player_uid: UUID | str) -> bool:
        pal_id = str(pal_id)
        player = self.get_player(player_uid)
        pal_entity = self.get_pal(pal_id)
        if not player or not pal_entity:
            return False
        target_group = self.group_data.get_group(player.group_id)
        if target_group is None:
            return False
        if not self.move_pal(pal_id, [player.PalStorageContainerId]):
            return False

        self.baseworker_mapping.pop(pal_id, None)
        self._dangling_pals.pop(pal_id, None)
        for other_player in self.get_players():
            if other_player is player:
                continue
            other_player.pop_pal(pal_id)
        pal_entity.OwnerPlayerUId = player.PlayerUId
        pal_entity.group_id = player.group_id
        for group in self.group_data.get_groups():
            if group is not target_group and group.has_pal(pal_entity.InstanceId):
                group.del_pal(pal_entity.InstanceId)
        if not target_group.has_pal(pal_entity.InstanceId):
            target_group.add_pal(pal_entity.InstanceId)
        if not player.get_pal(pal_id, disable_warning=True):
            player.add_pal(pal_entity)
        pal_entity.is_unreferenced_pal = False
        return True

    def delete_pal(self, guid: str | UUID) -> bool:
        guid = str(guid)
        pal = self.get_pal(guid)
        if not pal:
            LOGGER.warning(f"Can't find pal {guid}")
            return False

        if pal._pal_obj not in self._entities_list:
            LOGGER.error(f"Pal {guid} is missing from the world entity list.")
            return False

        try:
            for pal_group in self.group_data.get_groups():
                if pal_group.has_pal(pal.InstanceId):
                    pal_group.del_pal(pal.InstanceId)
            if pal_container := self.container_data.get_container(pal.ContainerId):
                pal_container.del_pal(pal.InstanceId)
            self._entities_list.remove(pal._pal_obj)
            self.baseworker_mapping.pop(guid, None)
            self._dangling_pals.pop(guid, None)
            for player in self.get_players():
                player.pop_pal(guid)
        except Exception:
            LOGGER.warning(f"Error Deleting PAL {guid}: {traceback.format_exc()}")
            return False
        LOGGER.info(f"DELETED PAL {guid}")
        return True

    def heal_all_pals(self) -> int:
        contexts = self.get_all_pal_contexts()
        for context in contexts:
            context["pal"].heal_pal()
        return len(contexts)

    def add_pal(
        self,
        player_uid: str | UUID,
        pal_obj: dict = None,
        character_id: str | None = None,
    ) -> Optional[PalEntity]:
        player = self.get_player(player_uid)
        if player is None:
            LOGGER.warning(f"Player {player_uid} not found")
            return None

        pal_container = self.container_data.get_container(player.PalStorageContainerId)
        if pal_container is not None and pal_container.get_empty_slot() == -1:
            pal_container = None

        if pal_container is None:
            LOGGER.info("No Empty Pal Slot")
            return None

        pal_instanceId = toUUID(str(uuid.uuid4()))
        group_id = player.group_id
        group = self.group_data.get_group(group_id)
        if group is None:
            LOGGER.error(f"Player {player_uid} has no writable guild group.")
            return None

        while pal_container.has_pal(pal_instanceId) or group.has_pal(pal_instanceId):
            pal_instanceId = toUUID(str(uuid.uuid4()))

        try:
            if (slot_idx := pal_container.add_pal(pal_instanceId)) == -1:
                return None
            container_id = pal_container.ID
            group.add_pal(pal_instanceId)

            if not pal_obj:
                pal_obj = PalObjects.PalSaveParameter(pal_instanceId, player_uid, container_id, slot_idx, group_id)
                pal_entity = PalEntity(pal_obj)
            else:
                pal_obj = copy.deepcopy(pal_obj)
                pal_entity = PalEntity(pal_obj)
                pal_entity.InstanceId = pal_instanceId
                pal_entity.SlotId = (container_id, slot_idx)
                pal_entity.OwnerPlayerUId = player_uid
                pal_entity.group_id = group_id
                # I don't know why some captured pals have PlayerUId,
                # But having non-empty ID will cause the game to hide the duped pal
                pal_entity.PlayerUId = PalObjects.EMPTY_UUID
                # It seems the item container id is not necessarily referenced in the ItemContainerSaveData
                # so just assign a randomly for now.
                pal_entity._pal_param["EquipItemContainerId"] = PalObjects.PalContainerId(str(uuid.uuid4()))
                # pal_entity._pal_param.pop("EquipItemContainerId", None)
                # remove expedition status
                pal_entity._pal_param.pop("MapObjectConcreteInstanceIdAssignedToExpedition", None)
                pal_entity.NickName = ""

            if character_id:
                pal_entity.CharacterID = character_id

            pal_entity.is_new_pal = True

            if not player.add_pal(pal_entity):
                raise Exception("Duplicated Pal ID, Try Again!")
            self._entities_list.append(pal_obj)
        except:
            try:
                pal_container.del_pal(pal_instanceId)
                group.del_pal(pal_instanceId)
            except Exception:
                pass
            LOGGER.error(f"Failed adding pal: {traceback.format_exc()}")
            return None
        LOGGER.info(f"Added Pal {pal_entity} to Player {player}")
        return pal_entity

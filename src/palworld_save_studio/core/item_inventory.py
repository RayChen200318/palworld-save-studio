from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import uuid
from typing import Any, Iterator

from palworld_save_tools.archive import UUID

from palworld_save_studio.utils.data_provider import DataProvider


ZERO_UUID = UUID.from_str("00000000-0000-0000-0000-000000000000")

CONTAINER_PROPERTIES = {
    "common": "CommonContainerId",
    "essential": "EssentialContainerId",
    "food": "FoodEquipContainerId",
    "weapon": "WeaponLoadOutContainerId",
    "armor": "PlayerEquipArmorContainerId",
    "drop": "DropSlotContainerId",
}

ARMOR_SLOT_TYPES = {
    0: "head",
    1: "body",
    2: "accessory",
    3: "accessory",
    4: "shield",
    5: "glider",
    6: "accessory",
    7: "accessory",
    8: "sphere-module",
}

COMMON_UNLOCKS = tuple(f"AdditionalInventory_{index:03d}" for index in range(1, 5))
FOOD_UNLOCKS = tuple(f"AutoMealPouch_Tier{index}" for index in range(1, 6))
WEAPON_UNLOCKS = ("UnlockEquipmentSlot_Weapon_01", "UnlockEquipmentSlot_Weapon_02")
ACCESSORY_UNLOCKS = (
    "UnlockEquipmentSlot_Accessory_01",
    "UnlockEquipmentSlot_Accessory_02",
)
CAPACITY_UNLOCKS = set(COMMON_UNLOCKS + FOOD_UNLOCKS + WEAPON_UNLOCKS + ACCESSORY_UNLOCKS)
PAL_GEAR_TYPE = "Essential_PalGear"

SLOT_CUSTOM_VERSION = bytes.fromhex(
    "020000007eb4ea129a1b5aff71aa71bcdf33d60e01000000"
    "380b00de4949d7ce97df2d99c0c1c36901000000"
)
DYNAMIC_CUSTOM_VERSIONS = {
    "armor": bytes.fromhex(
        "01000000380b00de4949d7ce97df2d99c0c1c36901000000"
    ),
    "weapon": bytes.fromhex(
        "020000005ce5d1372949215edc5ab593e15944e301000000"
        "380b00de4949d7ce97df2d99c0c1c36901000000"
    ),
    "egg": bytes.fromhex(
        "02000000380b00de4949d7ce97df2d99c0c1c36901000000"
        "6cf6fc0f99489011f89c60b15e47464a01000000"
    ),
}


class ItemInventoryError(ValueError):
    """A rejected item operation that must leave the draft unchanged."""


def _uuid_text(value: Any) -> str:
    return str(value).lower()


def _is_zero_uuid(value: Any) -> bool:
    return _uuid_text(value) == _uuid_text(ZERO_UUID)


def _is_pal_gear(item: dict[str, Any] | None) -> bool:
    return bool(item and item.get("TypeB") == PAL_GEAR_TYPE)


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, bytes):
        return {"bytes": value.hex()}
    if isinstance(value, UUID):
        return {"uuid": str(value)}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


class ItemInventoryService:
    """Mutates only a player's referenced item containers in the decoded Level.sav."""

    def __init__(self, save_manager: Any):
        self.manager = save_manager
        if save_manager.gvas_file is None:
            raise ItemInventoryError("No save is loaded.")
        self.world = save_manager.gvas_file.properties["worldSaveData"]["value"]
        self.container_property = self.world["ItemContainerSaveData"]
        self.dynamic_property = self.world["DynamicItemSaveData"]
        self.container_entries: list[dict[str, Any]] = self.container_property["value"]
        self.dynamic_entries: list[dict[str, Any]] = self.dynamic_property["value"]["values"]
        self._reindex()

    def _reindex(self) -> None:
        self.containers: dict[str, dict[str, Any]] = {}
        for entry in self.container_entries:
            container_id = _uuid_text(entry["key"]["ID"]["value"])
            if container_id in self.containers:
                raise ItemInventoryError(f"Duplicate item container ID: {container_id}")
            self.containers[container_id] = entry["value"]

        self.dynamic_records: dict[str, dict[str, Any]] = {}
        self.duplicate_dynamic_ids: set[str] = set()
        for entry in self.dynamic_entries:
            raw = entry["RawData"]["value"]
            dynamic_id = _uuid_text(raw["id"]["local_id_in_created_world"])
            if dynamic_id in self.dynamic_records:
                self.duplicate_dynamic_ids.add(dynamic_id)
            else:
                self.dynamic_records[dynamic_id] = entry

        self.dynamic_references: dict[str, list[tuple[str, int]]] = {}
        for container_id, container in self.containers.items():
            for slot in self._slot_values(container):
                raw = slot["RawData"]["value"]
                local_id = raw["item"]["dynamic_id"]["local_id_in_created_world"]
                if not _is_zero_uuid(local_id):
                    self.dynamic_references.setdefault(_uuid_text(local_id), []).append(
                        (container_id, int(raw["slot_index"]))
                    )

    @contextmanager
    def atomic(self) -> Iterator[None]:
        container_backup = copy.deepcopy(self.container_entries)
        dynamic_backup = copy.deepcopy(self.dynamic_entries)
        try:
            yield
            self._reindex()
        except Exception:
            self.container_entries[:] = container_backup
            self.dynamic_entries[:] = dynamic_backup
            self._reindex()
            raise

    @staticmethod
    def _slot_values(container: dict[str, Any]) -> list[dict[str, Any]]:
        return container["Slots"]["value"]["values"]

    @staticmethod
    def _slot_raw(slot: dict[str, Any]) -> dict[str, Any]:
        return slot["RawData"]["value"]

    def _player(self, player_id: str):
        player = self.manager.get_player(player_id)
        if player is None:
            raise ItemInventoryError(f"Player {player_id} was not found.")
        return player

    def _container_id(self, player: Any, container_name: str) -> str:
        if container_name not in CONTAINER_PROPERTIES:
            raise ItemInventoryError(f"Unknown player container: {container_name}")
        inventory = player._player_save_data.get("InventoryInfo", {}).get("value", {})
        reference = inventory.get(CONTAINER_PROPERTIES[container_name])
        try:
            return _uuid_text(reference["value"]["ID"]["value"])
        except (KeyError, TypeError) as exc:
            raise ItemInventoryError(
                f"The player's {container_name} container reference is missing."
            ) from exc

    def _container(self, player: Any, container_name: str) -> dict[str, Any]:
        container_id = self._container_id(player, container_name)
        container = self.containers.get(container_id)
        if container is None:
            raise ItemInventoryError(
                f"The player's {container_name} container {container_id} is missing."
            )
        return container

    def _slots_by_index(self, container: dict[str, Any]) -> dict[int, dict[str, Any]]:
        result: dict[int, dict[str, Any]] = {}
        slot_count = int(container["SlotNum"]["value"])
        for slot in self._slot_values(container):
            index = int(self._slot_raw(slot)["slot_index"])
            if index < 0 or index >= slot_count or index in result:
                raise ItemInventoryError("The item container has duplicate or invalid slots.")
            result[index] = slot
        return result

    def _player_static_ids(self, player: Any) -> set[str]:
        result: set[str] = set()
        for container_name in CONTAINER_PROPERTIES:
            container = self._container(player, container_name)
            for slot in self._slot_values(container):
                result.add(str(self._slot_raw(slot)["item"]["static_id"]))
        return result

    def unlocked_indices(self, player: Any, container_name: str) -> list[int]:
        container = self._container(player, container_name)
        physical_count = int(container["SlotNum"]["value"])
        owned = self._player_static_ids(player)
        if container_name == "common":
            capacity = min(54, 42 + 3 * sum(item in owned for item in COMMON_UNLOCKS))
            return list(range(min(physical_count, capacity)))
        if container_name == "food":
            capacity = sum(item in owned for item in FOOD_UNLOCKS)
            return list(range(min(physical_count, capacity)))
        if container_name == "weapon":
            capacity = 4 + sum(item in owned for item in WEAPON_UNLOCKS)
            return list(range(min(physical_count, capacity)))
        if container_name == "armor":
            indices = [0, 1, 2, 3, 4, 5, 8]
            if ACCESSORY_UNLOCKS[0] in owned:
                indices.append(6)
            if ACCESSORY_UNLOCKS[1] in owned:
                indices.append(7)
            return sorted(index for index in indices if index < physical_count)
        return list(range(physical_count))

    def _catalog_entry(self, static_id: str) -> dict[str, Any] | None:
        return DataProvider.get_item_data(static_id)

    @staticmethod
    def _validate_slot_index(slot_index: Any, label: str = "SlotIndex") -> int:
        if not isinstance(slot_index, int) or isinstance(slot_index, bool) or slot_index < 0:
            raise ItemInventoryError(f"{label} must be a non-negative integer.")
        return slot_index

    def _compatible(
        self,
        static_id: str,
        container_name: str,
        slot_index: int,
        *,
        unknown_original_container: str | None = None,
    ) -> bool:
        entry = self._catalog_entry(static_id)
        if entry is None:
            return container_name in {"common", unknown_original_container}
        if container_name not in entry["AllowedContainers"]:
            return False
        if container_name == "weapon":
            return entry.get("EquipSlot") == "weapon"
        if container_name == "armor":
            return entry.get("EquipSlot") == ARMOR_SLOT_TYPES.get(slot_index)
        return True

    def _assert_target(
        self,
        player: Any,
        container_name: str,
        slot_index: int,
        static_id: str,
        *,
        unknown_original_container: str | None = None,
    ) -> dict[str, Any]:
        self._validate_slot_index(slot_index)
        if container_name == "drop":
            raise ItemInventoryError("The temporary drop slots cannot be used as a target.")
        container = self._container(player, container_name)
        if slot_index not in self.unlocked_indices(player, container_name):
            raise ItemInventoryError("The target slot is locked or outside the container capacity.")
        if not self._compatible(
            static_id,
            container_name,
            slot_index,
            unknown_original_container=unknown_original_container,
        ):
            raise ItemInventoryError("The item is incompatible with the target slot.")
        return container

    def _slot(self, player: Any, container_name: str, slot_index: int) -> tuple[dict[str, Any], dict[str, Any]]:
        self._validate_slot_index(slot_index)
        container = self._container(player, container_name)
        slot = self._slots_by_index(container).get(slot_index)
        if slot is None:
            raise ItemInventoryError("The selected item slot is empty.")
        return container, slot

    def _dynamic_for_slot(self, slot: dict[str, Any]) -> dict[str, Any] | None:
        local_id = self._slot_raw(slot)["item"]["dynamic_id"]["local_id_in_created_world"]
        if _is_zero_uuid(local_id):
            return None
        return self.dynamic_records.get(_uuid_text(local_id))

    def _assert_dynamic_integrity(self, slot: dict[str, Any]) -> None:
        local_id = self._slot_raw(slot)["item"]["dynamic_id"]["local_id_in_created_world"]
        if _is_zero_uuid(local_id):
            return
        dynamic_id = _uuid_text(local_id)
        if dynamic_id in self.duplicate_dynamic_ids:
            raise ItemInventoryError("The item uses a duplicated dynamic UUID.")
        if dynamic_id not in self.dynamic_records:
            raise ItemInventoryError("The item's dynamic record is missing.")
        if len(self.dynamic_references.get(dynamic_id, [])) != 1:
            raise ItemInventoryError("The item's dynamic UUID has multiple slot references.")

    def _assert_mutable_item(self, slot: dict[str, Any]) -> None:
        static_id = str(self._slot_raw(slot)["item"]["static_id"])
        if DataProvider.get_item_managed_kind(static_id) == "system":
            raise ItemInventoryError(
                "System-managed progression records are read-only."
            )

    def _slot_payload(
        self, player: Any, container_name: str, index: int, slot: dict[str, Any] | None
    ) -> dict[str, Any]:
        unlocked = index in self.unlocked_indices(player, container_name)
        if slot is None:
            return {
                "Container": container_name,
                "SlotIndex": index,
                "SlotType": ARMOR_SLOT_TYPES.get(index) if container_name == "armor" else None,
                "Unlocked": unlocked,
                "Item": None,
            }

        raw = self._slot_raw(slot)
        static_id = str(raw["item"]["static_id"])
        catalog = self._catalog_entry(static_id)
        managed_kind = DataProvider.get_item_managed_kind(static_id)
        dynamic_id_value = raw["item"]["dynamic_id"]["local_id_in_created_world"]
        dynamic_id = None if _is_zero_uuid(dynamic_id_value) else _uuid_text(dynamic_id_value)
        dynamic = self.dynamic_records.get(dynamic_id) if dynamic_id else None
        dynamic_raw = dynamic["RawData"]["value"] if dynamic else None
        flags: list[str] = []
        if managed_kind == "system":
            flags.append("system-managed")
        elif catalog is None:
            flags.append("unknown-item")
        if _is_pal_gear(catalog) and int(raw["count"]) != 1:
            flags.append("invalid-quantity")
        if not unlocked:
            flags.append("locked-slot")
        if not self._compatible(static_id, container_name, index) and catalog is not None:
            flags.append("incompatible-slot")
        if dynamic_id:
            if dynamic_id in self.duplicate_dynamic_ids:
                flags.append("duplicate-dynamic-id")
            if dynamic is None:
                flags.append("missing-dynamic-record")
            if len(self.dynamic_references.get(dynamic_id, [])) != 1:
                flags.append("invalid-dynamic-reference")
            if dynamic_raw and dynamic_raw["id"].get("static_id") != static_id:
                flags.append("dynamic-static-id-mismatch")

        variants = []
        if catalog:
            variants = [
                {
                    "StaticId": variant["StaticId"],
                    "Rarity": variant["Rarity"],
                    "I18n": variant["I18n"],
                }
                for variant in DataProvider.get_item_variants(static_id)
            ]
        item_payload = {
            "StaticId": static_id,
            "ManagedKind": managed_kind,
            "I18n": catalog["I18n"] if catalog else {"en": static_id, "zh-CN": static_id},
            "IconKey": catalog["IconKey"] if catalog else None,
            "Category": catalog["Category"] if catalog else "unknown",
            "Quantity": int(raw["count"]),
            "MaxStack": catalog["MaxStack"] if catalog else None,
            "Rarity": catalog["Rarity"] if catalog else None,
            "Variants": variants,
            "DynamicId": dynamic_id,
            "DynamicType": dynamic_raw.get("type") if dynamic_raw else None,
            "Durability": dynamic_raw.get("durability") if dynamic_raw else None,
            "MaxDurability": catalog["MaxDurability"] if catalog else None,
            "Ammo": dynamic_raw.get("remaining_bullets") if dynamic_raw else None,
            "MagazineSize": catalog["MagazineSize"] if catalog else None,
            "PassiveSkills": list(dynamic_raw.get("passive_skill_list", [])) if dynamic_raw else [],
            "EggCharacterId": dynamic_raw.get("character_id") if dynamic_raw else None,
            "StateFlags": flags,
        }
        return {
            "Container": container_name,
            "SlotIndex": index,
            "SlotType": ARMOR_SLOT_TYPES.get(index) if container_name == "armor" else None,
            "Unlocked": unlocked,
            "Item": item_payload,
        }

    def player_inventory(self, player_id: str) -> dict[str, Any]:
        player = self._player(player_id)
        containers: dict[str, Any] = {}
        for name in CONTAINER_PROPERTIES:
            container = self._container(player, name)
            by_index = self._slots_by_index(container)
            physical_count = int(container["SlotNum"]["value"])
            if name == "drop":
                indices = sorted(by_index)
            else:
                indices = list(range(physical_count))
            slots = [self._slot_payload(player, name, index, by_index.get(index)) for index in indices]
            unlocked = self.unlocked_indices(player, name)
            containers[name] = {
                "ContainerId": self._container_id(player, name),
                "Capacity": len(unlocked),
                "PhysicalCapacity": physical_count,
                "UnlockedIndices": unlocked,
                "Slots": slots,
                "ReadOnlyTarget": name == "drop",
            }
        return {
            "PlayerId": str(player.PlayerUId),
            "PlayerName": player.NickName or str(player.PlayerUId),
            "Containers": containers,
        }

    @staticmethod
    def catalog() -> dict[str, Any]:
        data = DataProvider.get_item_catalog()
        items = {
            static_id: {**item, "ManagedKind": "normal"}
            for static_id, item in data["Items"].items()
        }
        species = []
        for pal in DataProvider.get_sorted_pals():
            internal_name = pal["InternalName"]
            if not DataProvider.is_editable_species(internal_name) or DataProvider.is_pal_human(internal_name):
                continue
            species.append(
                {
                    "CharacterId": internal_name,
                    "I18n": pal["I18n"],
                    "IconAccessKey": internal_name,
                }
            )
        return {
            "Source": data["Source"],
            "Items": items,
            "Groups": [
                {
                    **group,
                    "Variants": [
                        items[static_id]
                        for static_id in group["Variants"]
                        if static_id in items
                    ],
                }
                for group in data["Groups"]
            ],
            "EggSpecies": species,
        }

    def _new_dynamic(self, item: dict[str, Any], character_id: str | None) -> tuple[UUID, dict[str, Any]]:
        dynamic_type = item.get("DynamicType")
        if dynamic_type not in DYNAMIC_CUSTOM_VERSIONS:
            raise ItemInventoryError("This item does not use a supported dynamic record.")
        local_id = UUID.from_str(str(uuid.uuid4()))
        raw: dict[str, Any] = {
            "type": dynamic_type,
            "id": {
                "created_world_id": ZERO_UUID,
                "local_id_in_created_world": local_id,
                "static_id": item["StaticId"],
            },
            "leading_bytes": b"\x00" * 4,
        }
        if dynamic_type == "weapon":
            raw.update(
                durability=float(item["MaxDurability"]),
                remaining_bullets=0,
                passive_skill_list=[],
                unknown_str="None",
                trailing_bytes=b"\x00" * 4,
            )
        elif dynamic_type == "armor":
            raw.update(
                durability=float(item["MaxDurability"]),
                trailing_bytes=b"\x00" * 4,
            )
        else:
            if not isinstance(character_id, str) or not DataProvider.is_editable_species(character_id):
                raise ItemInventoryError("EggCharacterId must be a legal Palworld 1.0 species.")
            if DataProvider.is_pal_human(character_id):
                raise ItemInventoryError("Human NPCs cannot be placed inside Pal eggs.")
            raw.update(
                character_id=character_id,
                object={},
                trailing_bytes=b"\x00" * 28,
            )
        entry = {
            "RawData": {
                "array_type": "ByteProperty",
                "id": None,
                "value": raw,
                "type": "ArrayProperty",
                "custom_type": ".worldSaveData.DynamicItemSaveData.DynamicItemSaveData.RawData",
            },
            "CustomVersionData": {
                "array_type": "ByteProperty",
                "id": None,
                "value": {"values": DYNAMIC_CUSTOM_VERSIONS[dynamic_type]},
                "type": "ArrayProperty",
            },
        }
        return local_id, entry

    @staticmethod
    def _new_slot(index: int, static_id: str, count: int, dynamic_id: UUID) -> dict[str, Any]:
        return {
            "RawData": {
                "array_type": "ByteProperty",
                "id": None,
                "value": {
                    "slot_index": index,
                    "count": count,
                    "item": {
                        "static_id": static_id,
                        "dynamic_id": {
                            "created_world_id": ZERO_UUID,
                            "local_id_in_created_world": dynamic_id,
                        },
                    },
                    "trailing_bytes": b"\x00" * 20,
                },
                "type": "ArrayProperty",
                "custom_type": ".worldSaveData.ItemContainerSaveData.Value.Slots.Slots.RawData",
            },
            "CustomVersionData": {
                "array_type": "ByteProperty",
                "id": None,
                "value": {"values": SLOT_CUSTOM_VERSION},
                "type": "ArrayProperty",
            },
        }

    def add_item(
        self,
        player_id: str,
        static_id: str,
        container_name: str,
        quantity: int = 1,
        slot_index: int | None = None,
        egg_character_id: str | None = None,
    ) -> dict[str, Any]:
        player = self._player(player_id)
        item = self._catalog_entry(static_id)
        if item is None:
            raise ItemInventoryError("Only catalogued Palworld 1.0 items can be added.")
        static_id = item["StaticId"]
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ItemInventoryError("Quantity must be an integer.")
        if _is_pal_gear(item) and quantity != 1:
            raise ItemInventoryError("Pal Gear quantity must be exactly 1.")
        if item.get("DynamicType"):
            if quantity != 1:
                raise ItemInventoryError("Weapons, armor and eggs always have quantity 1.")
        elif quantity < 1 or quantity > int(item["MaxStack"]):
            raise ItemInventoryError(f"Quantity must be between 1 and {item['MaxStack']}.")
        container = self._container(player, container_name)
        occupied = self._slots_by_index(container)
        if slot_index is None:
            slot_index = next(
                (
                    index
                    for index in self.unlocked_indices(player, container_name)
                    if index not in occupied and self._compatible(static_id, container_name, index)
                ),
                None,
            )
        if slot_index is None:
            raise ItemInventoryError("No compatible empty slot is available.")
        self._validate_slot_index(slot_index)
        self._assert_target(player, container_name, slot_index, static_id)
        if slot_index in occupied:
            raise ItemInventoryError("The target slot is not empty.")

        with self.atomic():
            dynamic_id = ZERO_UUID
            if item.get("DynamicType"):
                dynamic_id, dynamic_entry = self._new_dynamic(item, egg_character_id)
                self.dynamic_entries.append(dynamic_entry)
            self._slot_values(container).append(
                self._new_slot(slot_index, static_id, quantity, dynamic_id)
            )
            self._slot_values(container).sort(key=lambda slot: self._slot_raw(slot)["slot_index"])
        return self.player_inventory(player_id)

    def patch_item(
        self,
        player_id: str,
        container_name: str,
        slot_index: int,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(changes, dict) or not changes:
            raise ItemInventoryError("Changes must be a non-empty object.")
        unknown = set(changes) - {"Quantity", "StaticId", "Durability", "Ammo"}
        if unknown:
            raise ItemInventoryError(f"Unsupported item fields: {', '.join(sorted(unknown))}")
        player = self._player(player_id)
        _, slot = self._slot(player, container_name, slot_index)
        self._assert_mutable_item(slot)
        self._assert_dynamic_integrity(slot)
        raw = self._slot_raw(slot)
        old_static_id = str(raw["item"]["static_id"])
        old_catalog = self._catalog_entry(old_static_id)

        with self.atomic():
            if "Quantity" in changes:
                quantity = changes["Quantity"]
                if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
                    raise ItemInventoryError("Quantity must be a positive integer.")
                if old_catalog:
                    if _is_pal_gear(old_catalog) and quantity != 1:
                        raise ItemInventoryError("Pal Gear quantity must be exactly 1.")
                    if quantity > int(old_catalog["MaxStack"]):
                        raise ItemInventoryError(
                            f"Quantity cannot exceed {old_catalog['MaxStack']}."
                        )
                    if old_catalog.get("DynamicType") and quantity != 1:
                        raise ItemInventoryError("Dynamic items always have quantity 1.")
                elif quantity > int(raw["count"]):
                    raise ItemInventoryError("A completely unknown item can only be reduced.")
                raw["count"] = quantity

            dynamic = self._dynamic_for_slot(slot)
            dynamic_raw = dynamic["RawData"]["value"] if dynamic else None
            catalog = old_catalog
            if "StaticId" in changes:
                new_static_id = changes["StaticId"]
                new_catalog = self._catalog_entry(new_static_id) if isinstance(new_static_id, str) else None
                if not old_catalog or not new_catalog:
                    raise ItemInventoryError("Unknown items cannot change rarity variants.")
                new_static_id = new_catalog["StaticId"]
                variants = {item["StaticId"] for item in DataProvider.get_item_variants(old_static_id)}
                if new_static_id not in variants:
                    raise ItemInventoryError("StaticId is not a formal variant of this item.")
                if new_catalog.get("DynamicType") != old_catalog.get("DynamicType"):
                    raise ItemInventoryError("The selected variant has an incompatible dynamic type.")
                if not self._compatible(new_static_id, container_name, slot_index):
                    raise ItemInventoryError("The selected variant is incompatible with this slot.")
                if dynamic_raw:
                    old_max = float(old_catalog.get("MaxDurability") or 0)
                    new_max = float(new_catalog.get("MaxDurability") or 0)
                    if "durability" in dynamic_raw:
                        ratio = float(dynamic_raw["durability"]) / old_max if old_max > 0 else 1.0
                        dynamic_raw["durability"] = max(0.0, min(new_max, ratio * new_max))
                    if "remaining_bullets" in dynamic_raw:
                        dynamic_raw["remaining_bullets"] = min(
                            int(dynamic_raw["remaining_bullets"]),
                            int(new_catalog.get("MagazineSize") or 0),
                        )
                    dynamic_raw["id"]["static_id"] = new_static_id
                raw["item"]["static_id"] = new_static_id
                catalog = new_catalog

            if "Durability" in changes:
                if not dynamic_raw or "durability" not in dynamic_raw or not catalog:
                    raise ItemInventoryError("This item has no editable durability.")
                durability = changes["Durability"]
                maximum = float(catalog.get("MaxDurability") or 0)
                if isinstance(durability, bool) or not isinstance(durability, (int, float)):
                    raise ItemInventoryError("Durability must be numeric.")
                if float(durability) < 0 or float(durability) > maximum:
                    raise ItemInventoryError(f"Durability must be between 0 and {maximum}.")
                dynamic_raw["durability"] = float(durability)

            if "Ammo" in changes:
                if not dynamic_raw or "remaining_bullets" not in dynamic_raw or not catalog:
                    raise ItemInventoryError("This item has no editable ammunition.")
                ammo = changes["Ammo"]
                maximum = int(catalog.get("MagazineSize") or 0)
                if not isinstance(ammo, int) or isinstance(ammo, bool) or ammo < 0 or ammo > maximum:
                    raise ItemInventoryError(f"Ammunition must be between 0 and {maximum}.")
                dynamic_raw["remaining_bullets"] = ammo
        return self.player_inventory(player_id)

    def _remove_dynamic_if_unreferenced(self, slot: dict[str, Any]) -> None:
        local_id = self._slot_raw(slot)["item"]["dynamic_id"]["local_id_in_created_world"]
        if _is_zero_uuid(local_id):
            return
        dynamic_id = _uuid_text(local_id)
        referenced = False
        for container in self.containers.values():
            for candidate in self._slot_values(container):
                candidate_id = self._slot_raw(candidate)["item"]["dynamic_id"]["local_id_in_created_world"]
                if _uuid_text(candidate_id) == dynamic_id:
                    referenced = True
                    break
            if referenced:
                break
        if referenced:
            return
        self.dynamic_entries[:] = [
            entry
            for entry in self.dynamic_entries
            if _uuid_text(entry["RawData"]["value"]["id"]["local_id_in_created_world"])
            != dynamic_id
        ]

    def _first_empty(
        self, player: Any, container_name: str, static_id: str
    ) -> tuple[dict[str, Any], int] | None:
        container = self._container(player, container_name)
        occupied = self._slots_by_index(container)
        for index in self.unlocked_indices(player, container_name):
            if index not in occupied and self._compatible(static_id, container_name, index):
                return container, index
        return None

    def _place_affected_slot(self, player: Any, slot: dict[str, Any], preferred: str) -> None:
        raw = self._slot_raw(slot)
        static_id = str(raw["item"]["static_id"])
        catalog = self._catalog_entry(static_id)
        is_stackable = catalog is not None and not catalog.get("DynamicType")
        if is_stackable:
            for target_name in (preferred, "common"):
                target_container = self._container(player, target_name)
                for target in self._slot_values(target_container):
                    target_raw = self._slot_raw(target)
                    if target_raw["item"]["static_id"] != static_id:
                        continue
                    available = int(catalog["MaxStack"]) - int(target_raw["count"])
                    if available <= 0:
                        continue
                    moved = min(available, int(raw["count"]))
                    target_raw["count"] += moved
                    raw["count"] -= moved
                    if raw["count"] == 0:
                        return
        for target_name in (preferred, "common"):
            destination = self._first_empty(player, target_name, static_id)
            if destination:
                target_container, target_index = destination
                raw["slot_index"] = target_index
                self._slot_values(target_container).append(slot)
                self._slot_values(target_container).sort(
                    key=lambda item: self._slot_raw(item)["slot_index"]
                )
                return
        raise ItemInventoryError("Removing this unlock item would leave no legal space for equipped items.")

    def _reorganize_locked_slots(self, player: Any) -> None:
        affected: list[tuple[str, dict[str, Any]]] = []
        for container_name in ("common", "food", "weapon", "armor"):
            container = self._container(player, container_name)
            unlocked = set(self.unlocked_indices(player, container_name))
            for slot in list(self._slot_values(container)):
                if int(self._slot_raw(slot)["slot_index"]) not in unlocked:
                    self._slot_values(container).remove(slot)
                    affected.append((container_name, slot))
        for preferred, slot in affected:
            self._place_affected_slot(player, slot, preferred)

    def delete_item(
        self,
        player_id: str,
        container_name: str,
        slot_index: int,
        confirm_dangerous: bool = False,
    ) -> dict[str, Any]:
        player = self._player(player_id)
        container, slot = self._slot(player, container_name, slot_index)
        self._assert_mutable_item(slot)
        self._assert_dynamic_integrity(slot)
        static_id = str(self._slot_raw(slot)["item"]["static_id"])
        catalog = self._catalog_entry(static_id)
        dangerous = bool(catalog and catalog["Category"] == "key") or static_id in CAPACITY_UNLOCKS
        if dangerous and confirm_dangerous is not True:
            raise ItemInventoryError("Deleting this key or unlock item requires explicit confirmation.")
        with self.atomic():
            self._slot_values(container).remove(slot)
            if static_id in CAPACITY_UNLOCKS:
                self._reorganize_locked_slots(player)
            self._remove_dynamic_if_unreferenced(slot)
        return self.player_inventory(player_id)

    def move_item(
        self,
        player_id: str,
        source_container: str,
        source_slot: int,
        target_container: str,
        target_slot: int,
    ) -> dict[str, Any]:
        self._validate_slot_index(source_slot, "Source SlotIndex")
        self._validate_slot_index(target_slot, "Target SlotIndex")
        if source_container == target_container and source_slot == target_slot:
            raise ItemInventoryError("Source and target slots must be different.")
        player = self._player(player_id)
        source, slot = self._slot(player, source_container, source_slot)
        self._assert_mutable_item(slot)
        self._assert_dynamic_integrity(slot)
        source_raw = self._slot_raw(slot)
        static_id = str(source_raw["item"]["static_id"])
        if source_container == "drop" and target_container != "common":
            raise ItemInventoryError("Drop-slot items can only be recovered to the common inventory.")
        target = self._assert_target(
            player,
            target_container,
            target_slot,
            static_id,
            unknown_original_container=source_container,
        )
        target_item = self._slots_by_index(target).get(target_slot)

        with self.atomic():
            if target_item is None:
                self._slot_values(source).remove(slot)
                source_raw["slot_index"] = target_slot
                self._slot_values(target).append(slot)
            else:
                self._assert_mutable_item(target_item)
                self._assert_dynamic_integrity(target_item)
                target_raw = self._slot_raw(target_item)
                target_static_id = str(target_raw["item"]["static_id"])
                source_dynamic = source_raw["item"]["dynamic_id"]["local_id_in_created_world"]
                target_dynamic = target_raw["item"]["dynamic_id"]["local_id_in_created_world"]
                catalog = self._catalog_entry(static_id)
                can_merge = (
                    target_static_id == static_id
                    and _is_zero_uuid(source_dynamic)
                    and _is_zero_uuid(target_dynamic)
                    and catalog is not None
                )
                if can_merge:
                    available = int(catalog["MaxStack"]) - int(target_raw["count"])
                    if available <= 0:
                        raise ItemInventoryError("The target stack is already full.")
                    moved = min(available, int(source_raw["count"]))
                    target_raw["count"] += moved
                    source_raw["count"] -= moved
                    if source_raw["count"] == 0:
                        self._slot_values(source).remove(slot)
                else:
                    if source_container == "drop":
                        raise ItemInventoryError("A drop-slot item cannot swap another item into the drop slot.")
                    if source_slot not in self.unlocked_indices(player, source_container):
                        raise ItemInventoryError("The source slot cannot receive a swapped item.")
                    if not self._compatible(
                        target_static_id,
                        source_container,
                        source_slot,
                        unknown_original_container=(
                            target_container if source_container == target_container else None
                        ),
                    ):
                        raise ItemInventoryError("The target item is incompatible with the source slot.")
                    self._slot_values(source).remove(slot)
                    self._slot_values(target).remove(target_item)
                    source_raw["slot_index"] = target_slot
                    target_raw["slot_index"] = source_slot
                    self._slot_values(target).append(slot)
                    self._slot_values(source).append(target_item)
            self._slot_values(source).sort(key=lambda item: self._slot_raw(item)["slot_index"])
            if target is not source:
                self._slot_values(target).sort(key=lambda item: self._slot_raw(item)["slot_index"])
        return self.player_inventory(player_id)

    def validate_integrity(self) -> None:
        """Validate every editable slot and its dynamic-record references."""

        self._reindex()
        if self.duplicate_dynamic_ids:
            raise ItemInventoryError("The save contains duplicated dynamic item UUIDs.")
        for player in self.manager.get_players():
            for container_name in CONTAINER_PROPERTIES:
                container = self._container(player, container_name)
                for slot in self._slots_by_index(container).values():
                    raw = self._slot_raw(slot)
                    static_id = raw.get("item", {}).get("static_id")
                    count = raw.get("count")
                    if not isinstance(static_id, str) or not static_id:
                        raise ItemInventoryError("An item slot has an invalid StaticId.")
                    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
                        raise ItemInventoryError("An item slot has an invalid quantity.")
                    self._assert_dynamic_integrity(slot)
                    dynamic = self._dynamic_for_slot(slot)
                    if dynamic is not None:
                        dynamic_static_id = dynamic["RawData"]["value"]["id"].get(
                            "static_id"
                        )
                        if dynamic_static_id != static_id:
                            raise ItemInventoryError(
                                "A dynamic item record does not match its slot StaticId."
                            )

    def semantic_snapshot(self) -> str:
        payload = {
            "containers": self.container_property,
            "dynamic": self.dynamic_property,
        }
        encoded = json.dumps(
            _canonical(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

"""Generate the offline Palworld 1.0 item catalog used by Save Studio.

The structural item metadata is pinned to a known Palworld Save Pal snapshot.
English/Chinese display names and icons are matched from the public PalDB item
lists.  The application never contacts either source at runtime.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup


METADATA_COMMIT = "d8907c4adfd4e9cae471e49b1c4bf5359f89402d"
METADATA_URL = (
    "https://raw.githubusercontent.com/oMaN-Rod/palworld-save-pal/"
    f"{METADATA_COMMIT}/data/json/items.json"
)
PALDB_URLS = {
    "en": "https://paldb.cc/en/Items",
    "zh-CN": "https://paldb.cc/cn/Items",
}
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Referer": "https://paldb.cc/",
}
VIRTUAL_PREFIXES = ("BossDefeatReward_",)
UNIQUE_UNLOCK_ITEMS = {
    *(f"AdditionalInventory_{index:03d}" for index in range(1, 5)),
    *(f"AutoMealPouch_Tier{index}" for index in range(1, 6)),
    *(f"UnlockEquipmentSlot_Accessory_{index:02d}" for index in range(1, 3)),
    *(f"UnlockEquipmentSlot_Weapon_{index:02d}" for index in range(1, 3)),
}


def _download_text(url: str) -> str:
    response = requests.get(url, headers=HTTP_HEADERS, timeout=60)
    response.raise_for_status()
    return response.text


def _load_text(path: Path | None, url: str) -> str:
    return path.read_text(encoding="utf-8") if path else _download_text(url)


def _parse_list(html: str) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_href: dict[str, dict[str, str]] = {}
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.select("a.itemname[data-hover]"):
        if anchor.find_parent("div", class_="flex-grow-1") is None:
            continue
        card = anchor.find_parent("div", class_="d-flex")
        if card is None:
            continue
        image = card.select_one("img")
        value = {
            "Name": anchor.get_text(" ", strip=True),
            "Href": anchor.get("href", ""),
            "IconUrl": image.get("src", "") if image else "",
        }
        by_href.setdefault(value["Href"], value)
        hover = unquote(anchor.get("data-hover", ""))
        if "?s=Items/" not in hover:
            continue
        internal_name = hover.split("?s=Items/", 1)[1].split("&", 1)[0]
        by_id.setdefault(internal_name, value)
    return by_id, by_href


def _category(metadata: dict[str, Any]) -> str:
    type_a = metadata.get("type_a", "")
    return {
        "Essential": "key",
        "Food": "food",
        "Weapon": "weapon",
        "SpecialWeapon": "weapon",
        "Armor": "armor",
        "Accessory": "accessory",
        "Glider": "glider",
        "SphereModule": "sphere-module",
        "Ammo": "ammo",
        "Material": "material",
        "Consume": "consume",
        "Blueprint": "blueprint",
    }.get(type_a, "other")


def _equip_slot(metadata: dict[str, Any]) -> str | None:
    type_a = metadata.get("type_a", "")
    group = metadata.get("group", "")
    if type_a in {"Weapon", "SpecialWeapon"}:
        return "weapon"
    if type_a == "Accessory":
        return "accessory"
    if type_a == "Glider":
        return "glider"
    if type_a == "SphereModule":
        return "sphere-module"
    if type_a == "Armor":
        return {
            "Head": "head",
            "Body": "body",
            "Shield": "shield",
        }.get(group)
    return None


def _allowed_containers(metadata: dict[str, Any]) -> list[str]:
    type_a = metadata.get("type_a", "")
    if type_a == "Essential":
        return ["essential"]
    result = ["common"]
    if type_a == "Food":
        result.append("food")
    elif _equip_slot(metadata):
        result.append("weapon" if _equip_slot(metadata) == "weapon" else "armor")
    return result


def _icon_key(url: str) -> str:
    return Path(urlparse(url).path).stem


def build_catalog(
    metadata: dict[str, dict[str, Any]],
    english_html: str,
    chinese_html: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    english_by_id, english_by_href = _parse_list(english_html)
    chinese_by_id, chinese_by_href = _parse_list(chinese_html)
    items: dict[str, dict[str, Any]] = {}
    icon_urls: dict[str, str] = {}

    for static_id, source in metadata.items():
        if source.get("disabled") or static_id.startswith(VIRTUAL_PREFIXES):
            continue
        english = english_by_id.get(static_id)
        chinese = chinese_by_id.get(static_id)
        href = (chinese or english or {}).get("Href", "")
        english = english or english_by_href.get(href)
        chinese = chinese or chinese_by_href.get(href)
        if not english or not chinese:
            raise RuntimeError(f"Missing PalDB localization for {static_id}")
        icon_url = english.get("IconUrl") or chinese.get("IconUrl")
        if not icon_url:
            raise RuntimeError(f"Missing PalDB icon for {static_id}")
        dynamic = source.get("dynamic") or {}
        icon_key = _icon_key(icon_url)
        icon_urls[icon_key] = icon_url
        items[static_id] = {
            "StaticId": static_id,
            "BaseKey": href or static_id,
            "I18n": {"en": english["Name"], "zh-CN": chinese["Name"]},
            "Category": _category(source),
            "TypeA": source.get("type_a", ""),
            "TypeB": source.get("type_b", ""),
            "EquipSlot": _equip_slot(source),
            "AllowedContainers": _allowed_containers(source),
            "Rarity": int(source.get("rarity", 0)),
            "Rank": int(source.get("rank", 0)),
            "SortId": int(source.get("sort_id", 0)),
            "MaxStack": 1
            if static_id in UNIQUE_UNLOCK_ITEMS
            else max(1, int(source.get("max_stack_count", 1))),
            "DynamicType": dynamic.get("type"),
            "MaxDurability": float(dynamic.get("durability", 0)),
            "MagazineSize": int(dynamic.get("magazine_size", 0)),
            "IconKey": icon_key,
        }

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items.values():
        grouped.setdefault(item["BaseKey"], []).append(item)
    groups = []
    for base_key, variants in grouped.items():
        variants.sort(key=lambda item: (item["Rarity"], item["Rank"], item["StaticId"]))
        representative = variants[0]
        groups.append(
            {
                "BaseKey": base_key,
                "I18n": representative["I18n"],
                "Category": representative["Category"],
                "IconKey": representative["IconKey"],
                "Variants": [item["StaticId"] for item in variants],
            }
        )
    groups.sort(key=lambda group: (items[group["Variants"][0]]["SortId"], group["BaseKey"]))
    return {
        "Source": {
            "PalworldSavePalCommit": METADATA_COMMIT,
            "PalDB": PALDB_URLS,
        },
        "Items": dict(sorted(items.items())),
        "Groups": groups,
    }, icon_urls


def _download_icon(target: Path, url: str) -> None:
    if target.exists():
        return
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = requests.get(url, headers=HTTP_HEADERS, timeout=60)
            response.raise_for_status()
            target.write_bytes(response.content)
            return
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Unable to download {url}") from last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-file", type=Path)
    parser.add_argument("--en-file", type=Path)
    parser.add_argument("--zh-file", type=Path)
    parser.add_argument("--data-output", type=Path)
    parser.add_argument("--icons-output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    data_output = args.data_output or root / "data" / "item_data.json"
    icons_output = args.icons_output or root / "icons" / "items"
    metadata = json.loads(_load_text(args.metadata_file, METADATA_URL))
    catalog, icon_urls = build_catalog(
        metadata,
        _load_text(args.en_file, PALDB_URLS["en"]),
        _load_text(args.zh_file, PALDB_URLS["zh-CN"]),
    )
    data_output.parent.mkdir(parents=True, exist_ok=True)
    data_output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    icons_output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(_download_icon, icons_output / f"{key}.webp", url)
            for key, url in icon_urls.items()
        ]
        for future in futures:
            future.result()
    print(f"Wrote {len(catalog['Items'])} items in {len(catalog['Groups'])} groups")
    print(f"Downloaded {len(icon_urls)} unique icons")


if __name__ == "__main__":
    main()

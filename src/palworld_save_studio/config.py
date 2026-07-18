import json
import os
from pathlib import Path
import sys
from typing import Optional
import aiohttp
import platform

def get_program_path():
    # If running in AppImage, use the real file path
    if "APPIMAGE" in os.environ:
        return Path(os.environ["APPIMAGE"]).parent
    elif getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.resolve()

PROGRAM_PATH = get_program_path()
if getattr(sys, "frozen", False):
    if hasattr(sys, "_MEIPASS"):
        ASSETS_PATH = Path(sys._MEIPASS)
    else:
        ASSETS_PATH = get_program_path()
else:
    ASSETS_PATH = get_program_path()

def get_app_data_path() -> Path:
    """Return the independent application-data directory used by Save Studio."""
    override = os.environ.get("PALWORLD_SAVE_STUDIO_DATA_DIR")
    if override:
        return Path(override)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "PalworldSaveStudio"
    return Path.home() / ".palworld-save-studio"


APP_DATA_PATH = get_app_data_path()
CONFIG_PATH = APP_DATA_PATH / "config.json"

VERSION = "0.1.0-beta.1"
RELEASE_TYPE = "BETA"
BUILD_TIME = "0000000001"
GIT_HASH = "0000000"
REPO = "undefined"

def version_info() -> str:
    if GIT_HASH == "0000000":
        return VERSION
    if RELEASE_TYPE == "NIGHTLY":
        return f"{VERSION}-{RELEASE_TYPE}-{GIT_HASH}-{REPO}-{BUILD_TIME}"
    if RELEASE_TYPE in {"BETA", "RELEASE"}:
        return f"{VERSION}-{RELEASE_TYPE}-{GIT_HASH}"
    return VERSION

def is_gh_build() -> bool:
    return GIT_HASH != "0000000"

async def get_new_version() -> Optional[tuple[str, str]]:
    if not is_gh_build():
        return None
    releases_url = "https://api.github.com/repos/RayChen200318/palworld-save-studio/releases/latest"
    async def fetch_latest_release():
        async with aiohttp.ClientSession() as session:
            async with session.get(releases_url) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()

    def get_platform_asset_name():
        sys_platform = platform.system()
        if sys_platform == "Windows":
            return "Windows"
        elif sys_platform == "Darwin":
            return "macOS"
        elif sys_platform == "Linux":
            return "Linux"
        return None

    def parse_version(tag):
        return tag

    async def check_update() -> Optional[tuple[str, str]]:
        release = await fetch_latest_release()
        if not release or "tag_name" not in release:
            return None
        latest_version = parse_version(release["tag_name"])
        current_version = VERSION
        if latest_version.lstrip("v") == current_version.lstrip("v"):
            return None
        platform_name = get_platform_asset_name()
        if not platform_name:
            return None
        for asset in release.get("assets", []):
            if platform_name in asset["name"]:
                return latest_version, asset["browser_download_url"]
        return None

    try:
        return await check_update()
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None


class Config:
    i18n: str = "zh-CN"
    mode: str = "gui"
    port: int = 58080
    debug: bool = False
    path: str = None
    password: str = None
    nocli: bool = False
    _password_hash: str = None
    JWT_SECRET_KEY: str = "X2Nvbm5sb3N0"

    @classmethod
    def load_from_file(cls, file_path: str=CONFIG_PATH):
        """Load configuration values from a JSON file using pathlib."""
        path = Path(file_path)
        if path.exists():
            with path.open("r") as file:
                data = json.load(file)
                for key, value in data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)

    @classmethod
    def set_configs(cls, attrs: dict):
        for key, value in attrs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        Config.save_to_file()

    @classmethod
    def set_config(cls, key, value):
        if hasattr(cls, key):
            setattr(cls, key, value)
        Config.save_to_file()

    @classmethod
    def save_to_file(cls, file_path: str=CONFIG_PATH):
        """Save current configuration values to a JSON file using the to_dict method and pathlib."""
        config_data = cls.to_dict()
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as file:
            json.dump(config_data, file, indent=4)

    @classmethod
    def __str__(cls):
        dic = cls.to_dict()
        attrs = [f"{key}: {dic[key]}" for key in dic]
        return ", ".join(attrs)

    @classmethod
    def to_dict(cls):
        return {
            'i18n': Config.i18n,
            'mode': Config.mode,
            'port': Config.port,
            'path': Config.path,
            'password': Config.password,
            'JWT_SECRET_KEY': Config.JWT_SECRET_KEY
        }

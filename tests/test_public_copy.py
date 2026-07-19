import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCopyTests(unittest.TestCase):
    def test_readme_and_ordinary_ui_have_no_old_marketing(self) -> None:
        frontend = ROOT / "frontend/src"
        readmes = [ROOT / "README.md", ROOT / "README.zh-CN.md"]
        ui_files = [
            path
            for path in frontend.rglob("*")
            if path.is_file()
            and path.suffix in {".ts", ".vue"}
            and not path.name.endswith(".test.ts")
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in readmes + ui_files)
        forbidden = re.compile(
            r"回退|安全写回|赞助|捐赠|discord|reversible|safe write-back|sponsor|donat",
            re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(text))

        ui_text = "\n".join(path.read_text(encoding="utf-8") for path in ui_files)
        self.assertNotIn("KrisCris", ui_text)
        for readme in readmes:
            self.assertIn(
                "https://github.com/KrisCris/Palworld-Pal-Editor",
                readme.read_text(encoding="utf-8"),
            )

    def test_legacy_frontend_calls_are_removed(self) -> None:
        frontend = ROOT / "frontend/src"
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in frontend.rglob("*")
            if path.is_file() and path.suffix in {".ts", ".vue"}
        )
        for legacy_path in ("/pal/paldata", "/pal/add_pal", "/pal/dupe_pal", "/player/player_data", "/save/save"):
            self.assertNotIn(legacy_path, text)


if __name__ == "__main__":
    unittest.main()

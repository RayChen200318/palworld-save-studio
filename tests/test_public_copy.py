import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCopyTests(unittest.TestCase):
    def test_readme_and_ordinary_ui_have_no_old_marketing(self) -> None:
        frontend = ROOT / "frontend/src"
        files = [ROOT / "README.md"] + [
            path
            for path in frontend.rglob("*")
            if path.is_file()
            and path.suffix in {".ts", ".vue"}
            and not path.name.endswith(".test.ts")
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        forbidden = re.compile(
            r"回退|安全写回|赞助|捐赠|discord|reversible|safe write-back|sponsor|donat|KrisCris",
            re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(text))

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

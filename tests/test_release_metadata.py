import json
from pathlib import Path
import tomllib
import unittest

from palworld_save_studio.config import VERSION
from palworld_save_studio.webui import SERVER_HOST


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_release_versions_are_synchronized(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as file:
            project_version = tomllib.load(file)["project"]["version"]
        with (ROOT / "frontend" / "package.json").open(encoding="utf-8") as file:
            frontend_version = json.load(file)["version"]

        self.assertEqual(VERSION, "0.4.3-beta.1")
        self.assertEqual(project_version, "0.4.3b1")
        self.assertEqual(frontend_version, VERSION)

    def test_beta_release_workflow_marks_hyphenated_tags_as_prerelease(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("$env:GITHUB_REF_NAME -match '-'", workflow)
        self.assertIn("--prerelease", workflow)
        self.assertIn("0.4.2 remains the latest stable release", workflow)

    def test_desktop_server_is_loopback_only(self) -> None:
        self.assertEqual(SERVER_HOST, "127.0.0.1")

    def test_windows_release_excludes_networked_developer_tools(self) -> None:
        build_script = (ROOT / "build_executable.ps1").read_text(encoding="utf-8")
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

        self.assertIn("assets/data;assets/data", build_script)
        self.assertIn("assets/icons;assets/icons", build_script)
        self.assertNotIn("assets;assets", build_script)
        self.assertNotIn("assets/tools", build_script)
        self.assertNotIn("aiohttp", requirements)


if __name__ == "__main__":
    unittest.main()

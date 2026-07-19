import importlib
import sys
from types import ModuleType
import unittest
from unittest.mock import patch


class EntrypointTests(unittest.TestCase):
    def test_packaged_entrypoint_imports_without_remote_web_mode(self) -> None:
        cli = ModuleType("palworld_save_studio.cli")
        cli.InteractThread = type("InteractThread", (), {"load": staticmethod(lambda: None)})
        cli.main = lambda: None
        gui = ModuleType("palworld_save_studio.gui")
        gui.main = lambda: None
        sys.modules.pop("palworld_save_studio.__main__", None)
        with patch.dict(
            sys.modules,
            {
                "palworld_save_studio.cli": cli,
                "palworld_save_studio.gui": gui,
            },
        ):
            module = importlib.import_module("palworld_save_studio.__main__")
        self.assertTrue(callable(module.main))
        self.assertFalse(hasattr(module, "webui_main"))


if __name__ == "__main__":
    unittest.main()

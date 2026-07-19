import unittest

from palworld_save_studio.config import version_key


class VersionOrderTests(unittest.TestCase):
    def test_older_public_beta_is_not_an_update_for_stable(self) -> None:
        self.assertLess(version_key("v0.1.0-beta.1"), version_key("0.3.0"))

    def test_prerelease_order_is_semantic(self) -> None:
        ordered = [
            "0.2.0-alpha.2",
            "0.2.0-beta.1",
            "0.2.0-beta.2",
            "0.2.0-rc.1",
            "0.2.0",
            "0.2.1-beta.1",
        ]
        self.assertEqual(sorted(ordered, key=version_key), ordered)

    def test_unsupported_tag_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            version_key("nightly-latest")


if __name__ == "__main__":
    unittest.main()

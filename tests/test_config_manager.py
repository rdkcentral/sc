import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from sc.config_manager import ConfigManager, MergePolicy
from sc.exceptions import ConfigError


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def test_resolves_relative_tool_paths_and_merges_nested_config(self):
        admin_main = self.root / "admin" / "config.yaml"
        user_main = self.root / "user" / "config.yaml"
        admin_main.parent.mkdir()
        user_main.parent.mkdir()

        admin_main.write_text("clone: tools/clone.yaml\n")
        user_main.write_text("clone: tools/clone.yaml\n")
        (admin_main.parent / "tools").mkdir()
        (user_main.parent / "tools").mkdir()
        (admin_main.parent / "tools" / "clone.yaml").write_text(
            "project_lists:\n  shared:\n    url: admin\n  admin_only:\n    url: admin\n"
        )
        (user_main.parent / "tools" / "clone.yaml").write_text(
            "project_lists:\n  shared:\n    url: user\n  user_only:\n    url: user\n"
        )

        with (
            patch("sc.config_manager.ADMIN_CONFIG_PATH", admin_main),
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
        ):
            manager = ConfigManager(
                "clone", {"project_lists": MergePolicy.PREFER_ADMIN}
            )

        self.assertEqual(
            manager.get_config(),
            {
                "project_lists": {
                    "shared": {"url": "admin"},
                    "admin_only": {"url": "admin"},
                    "user_only": {"url": "user"},
                }
            },
        )

    def test_update_creates_default_tool_directory(self):
        user_main = self.root / "config.yaml"

        with (
            patch(
                "sc.config_manager.ADMIN_CONFIG_PATH",
                self.root / "missing.yaml",
            ),
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
        ):
            manager = ConfigManager(
                "clone", {"project_lists": MergePolicy.PREFER_ADMIN}
            )
            manager.update_config(
                "project_lists", {"public": {"url": "example"}}
            )

        saved = yaml.safe_load(
            (self.root / "tools" / "clone.yaml").read_text()
        )
        self.assertEqual(
            saved,
            {"project_lists": {"public": {"url": "example"}}},
        )
        index = yaml.safe_load(user_main.read_text())
        self.assertEqual(
            index,
            {"config_version": 2, "clone": "tools/clone.yaml"},
        )

    def test_delete_key_removes_nested_user_value(self):
        user_main = self.root / "config.yaml"
        user_main.write_text("config_version: 2\ndocker: tools/docker.yaml\n")
        tool_path = self.root / "tools" / "docker.yaml"
        tool_path.parent.mkdir()
        tool_path.write_text(
            "registries:\n"
            "  ghcr.io/remove:\n"
            "    reg_type: github\n"
            "  ghcr.io/keep:\n"
            "    reg_type: github\n"
        )

        with (
            patch(
                "sc.config_manager.ADMIN_CONFIG_PATH",
                self.root / "missing.yaml",
            ),
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
        ):
            manager = ConfigManager(
                "docker", {"registries": MergePolicy.PREFER_ADMIN}
            )
            deleted = manager.delete_key_from_config(
                "registries", "ghcr.io/remove"
            )

        self.assertTrue(deleted)
        self.assertEqual(
            yaml.safe_load(tool_path.read_text()),
            {"registries": {"ghcr.io/keep": {"reg_type": "github"}}},
        )

    def test_delete_key_returns_false_for_missing_user_value(self):
        user_main = self.root / "config.yaml"
        user_main.write_text("config_version: 2\ndocker: tools/docker.yaml\n")

        with (
            patch(
                "sc.config_manager.ADMIN_CONFIG_PATH",
                self.root / "missing.yaml",
            ),
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
        ):
            manager = ConfigManager(
                "docker", {"registries": MergePolicy.PREFER_ADMIN}
            )

        self.assertFalse(
            manager.delete_key_from_config("registries", "ghcr.io/missing")
        )

    def test_migrates_legacy_user_config_to_split_files(self):
        user_main = self.root / "user" / "config.yaml"
        user_main.parent.mkdir()
        user_main.write_text(
            "clone:\n"
            "  public:\n"
            "    url: https://example.test/projects.yaml\n"
            "docker:\n"
            "  ghcr.io/example:\n"
            "    reg_type: github\n"
            "git_instances:\n"
            "  github.com:\n"
            "    provider: github\n"
            "ticketing_instances:\n"
            "  ABC:\n"
            "    provider: jira\n"
        )

        with (
            patch(
                "sc.config_manager.ADMIN_CONFIG_PATH",
                self.root / "missing.yaml",
            ),
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
        ):
            manager = ConfigManager(
                "clone", {"project_lists": MergePolicy.PREFER_ADMIN}
            )

        self.assertEqual(
            manager.get_config(),
            {
                "project_lists": {
                    "public": {
                        "url": "https://example.test/projects.yaml"
                    }
                }
            },
        )
        self.assertEqual(
            yaml.safe_load(user_main.read_text()),
            {
                "clone": "tools/clone.yaml",
                "docker": "tools/docker.yaml",
                "review": "tools/review.yaml",
                "config_version": 2,
            },
        )
        self.assertEqual(
            yaml.safe_load(
                (user_main.parent / "tools" / "docker.yaml").read_text()
            ),
            {
                "registries": {
                    "ghcr.io/example": {"reg_type": "github"}
                }
            },
        )
        self.assertEqual(
            yaml.safe_load(
                (user_main.parent / "tools" / "review.yaml").read_text()
            ),
            {
                "git_instances": {"github.com": {"provider": "github"}},
                "ticketing_instances": {"ABC": {"provider": "jira"}},
            },
        )

    def test_adds_version_to_an_unversioned_split_config(self):
        user_main = self.root / "config.yaml"
        user_main.write_text("clone: tools/clone.yaml\n")
        tool_path = self.root / "tools" / "clone.yaml"
        tool_path.parent.mkdir()
        tool_path.write_text("project_lists: {}\n")

        with (
            patch(
                "sc.config_manager.ADMIN_CONFIG_PATH",
                self.root / "missing.yaml",
            ),
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
        ):
            ConfigManager(
                "clone", {"project_lists": MergePolicy.PREFER_ADMIN}
            )

        self.assertEqual(
            yaml.safe_load(user_main.read_text()),
            {"clone": "tools/clone.yaml", "config_version": 2},
        )

    def test_rejects_config_from_a_newer_version(self):
        user_main = self.root / "config.yaml"
        user_main.write_text("config_version: 999\n")

        with (
            patch.dict(os.environ, {"SC_USER_CONFIG": str(user_main)}),
            self.assertRaisesRegex(ConfigError, "newer than supported"),
        ):
            ConfigManager("clone", {})

    def test_new_config_files_are_owner_readable_and_writable_only(self):
        config_path = self.root / "new" / "config.yaml"
        manager = ConfigManager.__new__(ConfigManager)

        manager._save_config(config_path, {"config_version": 2})

        self.assertEqual(config_path.stat().st_mode & 0o777, 0o600)

    def test_save_config_preserves_existing_file_mode(self):
        config_path = self.root / "config.yaml"
        config_path.write_text("config_version: 1\n")
        config_path.chmod(0o640)
        manager = ConfigManager.__new__(ConfigManager)

        manager._save_config(config_path, {"config_version": 2})

        self.assertEqual(config_path.stat().st_mode & 0o777, 0o640)
        self.assertEqual(
            yaml.safe_load(config_path.read_text()),
            {"config_version": 2},
        )


if __name__ == "__main__":
    unittest.main()

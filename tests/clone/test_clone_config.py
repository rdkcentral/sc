import unittest
from pathlib import Path
from unittest.mock import MagicMock

from sc.clone.clone_config import CloneConfigManager
from sc.clone.project_list.project_list_manager import ProjectListSource


class TestCloneConfigManager(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock()

    def test_get_project_lists_returns_only_clone_sources(self):
        self.config_manager.get_config.return_value = {
            "project_lists": {
                "public": {"url": "https://example.test/projects.yaml"}
            }
        }

        manager = CloneConfigManager(self.config_manager)

        self.assertEqual(
            manager.get_project_lists(),
            {"public": {"url": "https://example.test/projects.yaml"}},
        )

    def test_get_project_lists_defaults_to_empty_dict(self):
        self.config_manager.get_config.return_value = {}

        manager = CloneConfigManager(self.config_manager)

        self.assertEqual(manager.get_project_lists(), {})

    def test_add_project_list_updates_project_lists_section(self):
        source = ProjectListSource(url="https://example.test/projects.yaml")

        CloneConfigManager(self.config_manager).add_project_list("public", source)

        self.config_manager.update_config.assert_called_once_with(
            "project_lists",
            {"public": {"url": "https://example.test/projects.yaml"}},
        )

    def test_project_list_dir_is_next_to_user_config(self):
        self.config_manager.config_path = Path("/tmp/sc-user/config.yaml")

        manager = CloneConfigManager(self.config_manager)

        self.assertEqual(
            manager.project_list_dir,
            Path("/tmp/sc-user/project_lists"),
        )


if __name__ == "__main__":
    unittest.main()

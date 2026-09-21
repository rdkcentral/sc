import unittest
from unittest.mock import MagicMock

from sc.review.review_config import GitHostConfig, GitHostModel


class TestGitHostConfig(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock()
        self.git_config = GitHostConfig(self.config_manager)

    def test_get_patterns_returns_only_git_instances(self):
        self.config_manager.get_config.return_value = {
            "git_instances": {
                "github.com": {"token": "token", "provider": "github"}
            },
            "ticketing_instances": {"ABC": {}},
        }

        self.assertEqual(self.git_config.get_patterns(), {"github.com"})

    def test_get_returns_validated_git_host(self):
        self.config_manager.get_config.return_value = {
            "git_instances": {
                "github.com": {
                    "url": "https://api.github.com",
                    "token": "token",
                    "provider": "github",
                }
            }
        }

        self.assertEqual(
            self.git_config.get("github.com"),
            GitHostModel(
                url="https://api.github.com",
                token="token",
                provider="github",
            ),
        )

    def test_write_updates_git_instances_section(self):
        model = GitHostModel(token="token", provider="github")

        self.git_config.write("github.com", model)

        self.config_manager.update_config.assert_called_once_with(
            "git_instances",
            {"github.com": {"token": "token", "provider": "github"}},
        )


if __name__ == "__main__":
    unittest.main()

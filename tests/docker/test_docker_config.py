#!/usr/bin/env python3
from netrc import NetrcParseError
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sc.docker.docker_config import DockerConfigManager, RegistryConfig
from sc.docker.exceptions import NetrcError, ScDockerConfigError

class TestDockerConfigManager(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock()

    def create_manager(self, whitelist_content=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        whitelist_path = Path(temp_dir.name) / "docker_registry_whitelist"

        if whitelist_content is not None:
            whitelist_path.write_text(whitelist_content)

        return DockerConfigManager(
            config_manager=self.config_manager,
            whitelist_path=whitelist_path,
        )

    def test_get_whitelisted_registries(self):
        manager = self.create_manager(
            """
            ghcr.io/example
            artifactory.example.com/team
            """
        )

        self.assertEqual(
            manager.get_whitelisted_registries(),
            (
                "ghcr.io/example",
                "artifactory.example.com/team",
            ),
        )

    def test_whitelist_ignores_comments_and_blank_lines(self):
        manager = self.create_manager(
            """
            # comment

            ghcr.io/example

            # another comment
            artifactory.example.com/team
            """
        )

        self.assertEqual(
            manager.get_whitelisted_registries(),
            (
                "ghcr.io/example",
                "artifactory.example.com/team",
            ),
        )

    def test_missing_whitelist_allows_all_registries(self):
        manager = self.create_manager()

        self.assertEqual(manager.get_whitelisted_registries(), ())
        self.assertTrue(manager.registry_url_whitelisted("anything.example.com"))

    def test_registry_url_whitelisted_returns_true(self):
        manager = self.create_manager("ghcr.io/example")

        self.assertTrue(
            manager.registry_url_whitelisted("ghcr.io/example")
        )

    def test_registry_url_whitelisted_returns_false(self):
        manager = self.create_manager("ghcr.io/example")

        self.assertFalse(
            manager.registry_url_whitelisted("docker.io/example")
        )

    def test_get_all_registry_urls(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {},
            "artifactory.example.com/team": {},
        }

        manager = self.create_manager()

        self.assertEqual(
            manager.get_all_registry_urls(),
            [
                "ghcr.io/example",
                "artifactory.example.com/team",
            ],
        )

    def test_get_invalid_registries(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {},
            "docker.io/example": {},
        }

        manager = self.create_manager("ghcr.io/example")

        self.assertEqual(
            manager.get_invalid_registries(),
            ["docker.io/example"],
        )

    def test_get_invalid_registries_empty_when_whitelist_missing(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {},
            "docker.io/example": {},
        }

        manager = self.create_manager()

        self.assertEqual(manager.get_invalid_registries(), [])

    def test_get_registry_returns_none_when_not_configured(self):
        self.config_manager.get_config.return_value = {}

        manager = self.create_manager()

        self.assertIsNone(manager.get_registry("ghcr.io/example"))

    def test_get_registry_returns_config_credentials(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {
                "reg_type": "github",
                "credential_store": "config",
                "username": "user",
                "api_key": "token",
            }
        }

        manager = self.create_manager()

        registry = manager.get_registry("ghcr.io/example")

        self.assertEqual(
            registry,
            RegistryConfig(
                url="ghcr.io/example",
                reg_type="github",
                credential_store="config",
                username="user",
                api_key="token",
            ),
        )

    def test_get_registry_resolves_netrc_credentials(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {
                "reg_type": "github",
                "credential_store": "netrc",
            }
        }

        manager = self.create_manager()

        with patch.object(
            manager,
            "get_netrc_creds_by_registry",
            return_value=("netrc-user", "netrc-token"),
        ) as get_creds:
            registry = manager.get_registry("ghcr.io/example")

        get_creds.assert_called_once_with("ghcr.io/example")
        self.assertEqual(registry.username, "netrc-user")
        self.assertEqual(registry.api_key, "netrc-token")

    def test_get_registry_does_not_load_netrc_for_config_credentials(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {
                "reg_type": "github",
                "credential_store": "config",
                "username": "user",
                "api_key": "token",
            }
        }

        manager = self.create_manager()

        with patch.object(
            manager,
            "get_netrc_creds_by_registry",
        ) as get_creds:
            manager.get_registry("ghcr.io/example")

        get_creds.assert_not_called()

    def test_get_registry_rejects_non_whitelisted_registry(self):
        self.config_manager.get_config.return_value = {
            "docker.io/example": {
                "reg_type": "github",
                "credential_store": "config",
            }
        }

        manager = self.create_manager("ghcr.io/example")

        with self.assertRaisesRegex(
            ScDockerConfigError,
            "Registry 'docker.io/example' is not whitelisted",
        ):
            manager.get_registry("docker.io/example")

    def test_get_all_registries(self):
        self.config_manager.get_config.return_value = {
            "ghcr.io/example": {
                "reg_type": "github",
                "credential_store": "config",
                "username": "user",
                "api_key": "token",
            },
            "artifactory.example.com/team": {
                "reg_type": "artifactory",
                "credential_store": "config",
                "username": "other",
                "api_key": "secret",
            },
        }

        manager = self.create_manager()

        registries = manager.get_all_registries()

        self.assertEqual(len(registries), 2)
        self.assertEqual(registries[0].url, "ghcr.io/example")
        self.assertEqual(
            registries[1].url,
            "artifactory.example.com/team",
        )

    def test_delete_registry(self):
        manager = self.create_manager()

        manager.delete_registry("ghcr.io/example")

        self.config_manager.delete_key_from_config.assert_called_once_with(
            "ghcr.io/example"
        )

    def test_delete_registry_does_not_require_whitelist_validation(self):
        manager = self.create_manager("ghcr.io/example")

        manager.delete_registry("invalid.example.com")

        self.config_manager.delete_key_from_config.assert_called_once_with(
            "invalid.example.com"
        )

    def test_add_registry_with_config_credentials(self):
        manager = self.create_manager()

        manager.add_registry(
            registry_url="ghcr.io/example",
            registry_type="github",
            credential_store="config",
            username="user",
            api_token="token",
        )

        self.config_manager.update_config.assert_called_once_with(
            {
                "ghcr.io/example": {
                    "reg_type": "github",
                    "credential_store": "config",
                    "username": "user",
                    "api_key": "token",
                }
            }
        )

    def test_add_registry_with_netrc_does_not_store_credentials(self):
        manager = self.create_manager()

        manager.add_registry(
            registry_url="ghcr.io/example",
            registry_type="github",
            credential_store="netrc",
            username="user",
            api_token="token",
        )

        self.config_manager.update_config.assert_called_once_with(
            {
                "ghcr.io/example": {
                    "reg_type": "github",
                    "credential_store": "netrc",
                }
            }
        )

    def test_add_registry_rejects_non_whitelisted_registry(self):
        manager = self.create_manager("ghcr.io/example")

        with self.assertRaises(ScDockerConfigError):
            manager.add_registry(
                registry_url="docker.io/example",
                registry_type="github",
                credential_store="config",
            )

        self.config_manager.update_config.assert_not_called()

    def test_add_registry_wraps_config_manager_error(self):
        self.config_manager.update_config.side_effect = OSError("write failed")

        manager = self.create_manager()

        with self.assertRaisesRegex(
            ScDockerConfigError,
            "Failed to write to config write failed",
        ) as context:
            manager.add_registry(
                registry_url="ghcr.io/example",
                registry_type="github",
                credential_store="config",
            )

        self.assertIsInstance(context.exception.__cause__, OSError)

    def test_validate_registry_error_contains_allowed_registries(self):
        manager = self.create_manager(
            """
            ghcr.io/example
            artifactory.example.com/team
            """
        )

        with self.assertRaises(ScDockerConfigError) as context:
            manager.get_registry("docker.io/example")

        message = str(context.exception)

        self.assertIn(
            "Registry 'docker.io/example' is not whitelisted",
            message,
        )
        self.assertIn("Allowed registries:", message)
        self.assertIn("- ghcr.io/example", message)
        self.assertIn(
            "- artifactory.example.com/team",
            message,
        )


class TestDockerConfigManagerNetrc(unittest.TestCase):

    def setUp(self):
        self.config_manager = MagicMock()
        self.manager = DockerConfigManager(
            config_manager=self.config_manager,
            whitelist_path=Path("/path/that/does/not/exist"),
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("sc.docker.docker_config.netrc")
    def test_get_netrc_credentials_from_default_file(self, mock_netrc):
        netrc_instance = mock_netrc.return_value
        netrc_instance.authenticators.return_value = (
            "user",
            None,
            "token",
        )

        result = self.manager.get_netrc_creds_by_registry(
            "ghcr.io/example"
        )

        self.assertEqual(result, ("user", "token"))
        mock_netrc.assert_called_once_with()
        netrc_instance.authenticators.assert_called_once_with("ghcr.io")

    @patch.dict(
        os.environ,
        {"NETRC_PATH": "/custom/path/.netrc"},
        clear=True,
    )
    @patch("sc.docker.docker_config.netrc")
    def test_get_netrc_credentials_from_custom_path(self, mock_netrc):
        netrc_instance = mock_netrc.return_value
        netrc_instance.authenticators.return_value = (
            "user",
            None,
            "token",
        )

        result = self.manager.get_netrc_creds_by_registry(
            "artifactory.example.com/team"
        )

        self.assertEqual(result, ("user", "token"))
        mock_netrc.assert_called_once_with("/custom/path/.netrc")
        netrc_instance.authenticators.assert_called_once_with(
            "artifactory.example.com"
        )

    @patch("sc.docker.docker_config.netrc")
    def test_get_netrc_credentials_missing_machine(self, mock_netrc):
        mock_netrc.return_value.authenticators.return_value = None

        with self.assertRaisesRegex(
            NetrcError,
            "No authenticators found for machine 'ghcr.io'",
        ):
            self.manager.get_netrc_creds_by_registry(
                "ghcr.io/example"
            )

    @patch("sc.docker.docker_config.netrc")
    def test_get_netrc_credentials_handles_missing_file(self, mock_netrc):
        mock_netrc.side_effect = FileNotFoundError(
            "No such file or directory"
        )

        with self.assertRaisesRegex(NetrcError, ".netrc file not found"):
            self.manager.get_netrc_creds_by_registry(
                "ghcr.io/example"
            )

    @patch("sc.docker.docker_config.netrc")
    def test_get_netrc_credentials_handles_parse_error(self, mock_netrc):
        mock_netrc.side_effect = NetrcParseError(
            "bad netrc",
            "/home/user/.netrc",
            1,
        )

        with self.assertRaisesRegex(NetrcError, "Failed to grab credentials from your .netrc"):
            self.manager.get_netrc_creds_by_registry(
                "ghcr.io/example"
            )

if __name__ == "__main__":
    unittest.main()

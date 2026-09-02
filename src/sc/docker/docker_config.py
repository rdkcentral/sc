# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Manages docker portion of sc config and the docker registry whitelist."""

from netrc import netrc, NetrcParseError
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from .exceptions import ScDockerConfigError, NetrcError
from sc.config_manager import ConfigManager

REGISTRY_WHITELIST = Path("/etc/sc/docker_registry_whitelist")

class RegistryConfig(BaseModel):
    url: str
    reg_type: Literal["github", "artifactory"]
    credential_store: Literal["config", "netrc"]
    username: str | None = None
    api_key: str | None = None

class DockerConfigManager:
    """Manages the docker portion of config in ~/.sc_config/config.yaml and the
    docker registry whitelist.

    The layout is keys are registry urls (ghcr.io/org) and the values are
    RegistryConfig models.
    """
    def __init__(
            self,
            config_manager: ConfigManager | None = None,
            whitelist_path: Path = REGISTRY_WHITELIST):
        self._docker_config_manager = config_manager or ConfigManager('docker')
        self._whitelist_path = whitelist_path
        self._whitelisted_registries = self._load_whitelisted_registries()

    def get_whitelisted_registries(self) -> tuple[str, ...]:
        """Returns a tuple of whitelisted registries. If the tuple is empty all
        registries are valid.
        """
        return self._whitelisted_registries

    def is_registry_allowed(self, registry_url: str) -> bool:
        if not self._whitelisted_registries or registry_url in self._whitelisted_registries:
            return True
        return False

    def list_registry_urls(self) -> list[str]:
        """Return all registry URLs defined in the config."""
        return list(self._docker_config_manager.get_config().keys())

    def get_registry(self, registry_url: str) -> RegistryConfig | None:
        """Get registry config for a registry by its URL with netrc credentials resolved.

        Raises:
            NetrcError: If a problem occurs while trying to load credentials from .netrc
        """
        self._validate_registry_url(registry_url)

        config = self._docker_config_manager.get_config().get(registry_url)

        if config is None:
            return None

        registry = RegistryConfig.model_validate({"url": registry_url, **config})

        if registry.credential_store == "netrc":
            registry.username, registry.api_key = self.get_netrc_creds_by_registry(registry_url)

        return registry

    def delete_registry(self, registry_url: str):
        self._docker_config_manager.delete_key_from_config(registry_url)

    def add_registry(
            self,
            registry_url: str,
            registry_type: Literal["github", "artifactory"],
            credential_store: Literal["config", "netrc"],
            username: str | None = None,
            api_key: str | None = None
        ):
        """Add a registry to the config.

        Raises:
            ScDockerConfigError: If an error occurs writing to the config
        """
        self._validate_registry_url(registry_url)

        config_dict = {
            registry_url: {
                "reg_type": registry_type,
                "credential_store": credential_store,
            }
        }

        if credential_store == "config":
            if not username or not api_key:
                raise ScDockerConfigError(
                    "username and api_key required when adding registry with store 'config'")
            config_dict[registry_url]["username"] = username
            config_dict[registry_url]["api_key"] = api_key

        try:
            self._docker_config_manager.update_config(config_dict)
        except Exception as e:
            raise ScDockerConfigError(f"Failed to write to config {str(e)}") from e

    def get_netrc_creds_by_registry(self, registry_url: str) -> tuple[str, str]:
        try:
            netrc_path = os.getenv('NETRC_PATH')
            creds = netrc(netrc_path) if netrc_path else netrc()

            machine = registry_url.split("/")[0]
            auth = creds.authenticators(machine)
            if not auth:
                raise NetrcError(f"No authenticators found for machine '{machine}' in .netrc")
            username, _, api_key = auth
            if not username or not api_key:
                raise NetrcError(f"Incomplete authenticators for machine '{machine}' in .netrc")
            return username, api_key
        except NetrcParseError as e:
            raise NetrcError(
                f"Failed to grab credentials from your .netrc: {e} \n"
                "You may have to run command: chmod 600 ~/.netrc"
            ) from e
        except FileNotFoundError as e:
            raise NetrcError(f".netrc file not found: {e}") from e
        except OSError as e:
            raise NetrcError(f".netrc failed to load: {e}") from e

    def _validate_registry_url(self, registry_url: str):
        """Raise ScDockerConfigError if the registry url provided is not whitelisted."""
        if not self.is_registry_allowed(registry_url):
            error_msg = [f"Registry '{registry_url}' is not whitelisted"]
            error_msg.append("Allowed registries:")
            for reg in self._whitelisted_registries:
                error_msg.append(f"- {reg}")
            raise ScDockerConfigError("\n".join(error_msg))

    def _load_whitelisted_registries(self) -> tuple[str, ...]:
        """Load registries from whitelist file and remove comments (lines starting with #)"""
        if self._whitelist_path.exists():
            with self._whitelist_path.open('r') as file:
                stripped_lines = [line.strip() for line in file]
                return tuple(line for line in stripped_lines if line and not line.startswith("#"))
        return ()

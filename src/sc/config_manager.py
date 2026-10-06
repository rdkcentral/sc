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

from enum import Enum
import os
from pathlib import Path
import stat
import tempfile

import yaml

from .exceptions import ConfigError

ADMIN_CONFIG_DIR = Path("/etc/sc")
ADMIN_CONFIG_PATH = ADMIN_CONFIG_DIR / "config.yaml"
USER_CONFIG_DIR = Path().home() / ".sc_config"
USER_DEFAULT_CONFIG_PATH = USER_CONFIG_DIR / "config.yaml"
CONFIG_VERSION_KEY = "config_version"
CURRENT_CONFIG_VERSION = 2

# Version 1 stored each section directly in the main config. This maps each
# legacy section to its version 2 tool file and the section within that file.
LEGACY_CONFIG_LOCATIONS = {
    "clone": ("clone", "project_lists"),
    "docker": ("docker", "registries"),
    "git_instances": ("review", "git_instances"),
    "ticketing_instances": ("review", "ticketing_instances"),
}

class MergePolicy(Enum):
    ADMIN_ONLY = "admin_only"
    PREFER_ADMIN = "prefer_admin"

class ConfigManager:
    """Load and merge one tool's user and administrator configuration.

    The user and administrator index files link to separate YAML files for each
    tool. Merge policies apply to the top-level sections within that tool file.
    Only the user tool file can be changed through this manager.
    """
    def __init__(self, tool: str, merge_policy: dict[str, MergePolicy]):
        """Load and merge a tool's configuration files.

        Args:
            tool: Name used to find the tool file in each configuration index.
            merge_policy: Merge behavior keyed by section in the tool file.
        """
        self.tool = tool
        self._merge_policy = merge_policy

        self._user_config_path = Path(os.getenv("SC_USER_CONFIG", USER_DEFAULT_CONFIG_PATH))
        self._admin_config_path = ADMIN_CONFIG_PATH
        self._migrate_user_config()

        self._user_tool_config_path = self._get_tool_config_path(
            self._user_config_path,
            tool,
            self._user_config_path.parent / "tools" / f"{tool}.yaml",
        )
        self._admin_tool_config_path = self._get_tool_config_path(self._admin_config_path, tool)

        self._user_tool_config = self._load_config(self._user_tool_config_path)
        self._admin_tool_config = self._load_config(self._admin_tool_config_path)

        self._effective_config = self._merge_config()

    @property
    def config_path(self) -> Path:
        """Return the path to the user configuration index."""
        return self._user_config_path

    def get_config(self) -> dict:
        """Return the effective configuration for this tool."""
        return self._effective_config

    def update_config(self, key: str, updates: dict):
        """Shallow-update a section in the user tool configuration."""
        self._user_tool_config.setdefault(key, {}).update(updates)
        self._save_user_tool_config()
        self._effective_config = self._merge_config()

    def delete_key_from_config(self, section: str, key: str) -> bool:
        """Delete a key from a user section, returning whether it existed.

        Administrator values cannot be deleted. If the administrator config
        defines the same key, its value becomes effective after the user value
        is removed.
        """
        user_section = self._user_tool_config.get(section)

        if not isinstance(user_section, dict) or key not in user_section:
            return False

        del user_section[key]
        if not user_section:
            del self._user_tool_config[section]
        self._save_user_tool_config()
        self._effective_config = self._merge_config()
        return True

    def _get_tool_config_path(
        self,
        config_path: Path,
        tool: str,
        default_path: Path | None = None
    ) -> Path | None:
        if config_path.exists():
            with config_path.open() as f:
                data = yaml.safe_load(f)

            if isinstance(data, dict) and tool in data:
                tool_path = Path(data[tool]).expanduser()
                if not tool_path.is_absolute():
                    tool_path = config_path.parent / tool_path
                return tool_path

        return default_path

    def _load_config(self, path: Path | None) -> dict:
        if path is None or not path.exists():
            return {}

        with path.open() as f:
            data = yaml.safe_load(f)

        if data is None or not isinstance(data, dict):
            return {}

        return data

    def _migrate_user_config(self) -> None:
        """Upgrade the user's monolithic config to the split-file layout.

        Admin configuration is intentionally not migrated here. The main user
        config is written last so an interrupted migration can safely be run
        again on the next invocation.
        """
        if not self._user_config_path.exists():
            return

        config = self._load_config(self._user_config_path)
        version = config.get(CONFIG_VERSION_KEY, 1)
        if not isinstance(version, int):
            raise ConfigError(f"Invalid user config version: {version!r}")
        if version > CURRENT_CONFIG_VERSION:
            raise ConfigError(
                f"User config version {version} is newer than supported version "
                f"{CURRENT_CONFIG_VERSION}"
            )
        if version == CURRENT_CONFIG_VERSION:
            return

        migrated_config = {}
        migrated_tools = {}
        for legacy_section, section_config in config.items():
            if legacy_section == CONFIG_VERSION_KEY:
                continue

            if not isinstance(section_config, dict):
                # This entry is already a link to a split tool config.
                migrated_config[legacy_section] = section_config
                continue

            tool, section = LEGACY_CONFIG_LOCATIONS.get(
                legacy_section, (legacy_section, None)
            )
            relative_path = Path("tools") / f"{tool}.yaml"
            migrated_config[tool] = str(relative_path)
            if section is None:
                migrated_tools.setdefault(tool, {}).update(section_config)
            else:
                migrated_tools.setdefault(tool, {})[section] = section_config

        for tool, tool_config in migrated_tools.items():
            tool_path = self._user_config_path.parent / "tools" / f"{tool}.yaml"
            self._save_config(tool_path, tool_config)

        migrated_config[CONFIG_VERSION_KEY] = CURRENT_CONFIG_VERSION
        self._save_config(self._user_config_path, migrated_config)

    def _merge_config(self) -> dict:
        result = {}
        for key in self._admin_tool_config.keys() | self._user_tool_config.keys():
            policy = self._merge_policy.get(key, MergePolicy.ADMIN_ONLY)
            admin = self._admin_tool_config.get(key)
            user = self._user_tool_config.get(key)

            match policy:
                case MergePolicy.ADMIN_ONLY:
                    if key in self._admin_tool_config:
                        result[key] = admin

                case MergePolicy.PREFER_ADMIN:
                    result[key] = {**(user or {}), **(admin or {})}

        return result

    def _save_user_tool_config(self):
        self._save_config(self._user_tool_config_path, self._user_tool_config)
        self._save_user_config_index()

    def _save_user_config_index(self) -> None:
        config = self._load_config(self._user_config_path)
        config[CONFIG_VERSION_KEY] = CURRENT_CONFIG_VERSION
        if self.tool not in config:
            try:
                tool_path = self._user_tool_config_path.relative_to(
                    self._user_config_path.parent
                )
            except ValueError:
                tool_path = self._user_tool_config_path
            config[self.tool] = str(tool_path)
        self._save_config(self._user_config_path, config)

    def _save_config(self, path: Path, config: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        file_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
        )
        temporary_path = Path(temporary_name)

        try:
            with os.fdopen(file_descriptor, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
                f.flush()
                os.fsync(f.fileno())

            temporary_path.chmod(file_mode)
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)

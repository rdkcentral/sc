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

import yaml

from .exceptions import ConfigError

ADMIN_CONFIG_DIR = Path("/etc/sc")
ADMIN_CONFIG_PATH = ADMIN_CONFIG_DIR / "config.yaml"
USER_CONFIG_DIR = Path().home() / ".sc_config"
USER_DEFAULT_CONFIG_PATH = USER_CONFIG_DIR / "config.yaml"

class MergePolicy(Enum):
    ADMIN_ONLY = "admin_only"
    PREFER_ADMIN = "prefer_admin"

class ConfigManager:
    """
    Manages sc configurations by loading a user and an admin yaml file, merging a specific
    section, and allowing modifications only to the users config.
    """
    def __init__(self, tool: str, merge_policy: dict[str, MergePolicy]):
        """Loads configuration files and merges a tools subconfig.

        Args:
            tool (str): A tool which has it's own subconfig.
        """
        self.tool = tool
        self._merge_policy = merge_policy

        self._user_config_path = Path(os.getenv("SC_USER_CONFIG", USER_DEFAULT_CONFIG_PATH))
        self._admin_config_path = ADMIN_CONFIG_PATH

        self._user_tool_config_path = self._get_tool_config_path(
            self._user_config_path, tool, USER_CONFIG_DIR / "tools" / f"{tool}.yaml")
        self._admin_tool_config_path = self._get_tool_config_path(self._admin_config_path, tool)

        self._user_tool_config = self._load_config(self._user_tool_config_path)
        self._admin_tool_config = self._load_config(self._admin_tool_config_path)

        self._effective_config = self._merge_config()

    @property
    def config_path(self) -> Path:
        return self._user_config_path

    def get_config(self) -> dict:
        """Returns the merged section."""
        return self.merged_section

    def update_config(self, key: str, updates: dict):
        """Updates the user config's section and writes it back."""
        self._user_tool_config.setdefault(key, {}).update(updates)
        self._save_user_tool_config()
        self.merged_section = self._merge_config()

    def delete_key_from_config(self, key: str) -> bool:
        """Deletes a key from the user config's section and writes it back."""
        if key not in self._user_tool_config:
            return False

        del self._user_tool_config[key]
        self._save_user_tool_config()
        self.merged_section = self._merge_config()
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
                return Path(data[tool])

        return default_path

    def _load_config(self, path: Path | None) -> dict:
        if path is None or not path.exists():
            return {}

        with path.open() as f:
            data = yaml.safe_load(f)

        if data is None or not isinstance(data, dict):
            return {}

        return data

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

    def _save_user_tool_config(self):
        with open(self._user_tool_config_path, "w") as f:
            yaml.dump(self._user_tool_config, f, default_flow_style=False, sort_keys=False)

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

import os
from pathlib import Path

import yaml

class ConfigManager:
    """
    Manages sc configurations by loading a user and an admin yaml file, merging a specific
    section, and allowing modifications only to the users config.
    """
    def __init__(
            self, 
            section: str
        ):
        """Loads configuration files and merges a specific section.

        Args:
            section (str): Section to merge and perform actions on.
        """        
        self.section = section

        self._sc_config_dir = Path.home() / ".sc_config"
        self._user_config_path = Path(
            os.getenv("SC_USER_CONFIG", self._sc_config_dir / "config.yaml"))
        self._admin_config_path = Path("/etc/sc/config.yaml")

        self._user_config = self._load_config(self._user_config_path)
        self._admin_config = self._load_config(self._admin_config_path)
        
        self.merged_section = self._merge_section()
    
    @property
    def config_path(self) -> Path:
        return self._user_config_path
    
    @property
    def config_dir(self) -> Path:
        return self._sc_config_dir

    def get_config(self) -> dict:
        """Returns the merged section."""
        return self.merged_section

    def update_config(self, updates: dict):
        """Updates the user config's section and writes it back."""
        if self.section not in self._user_config:
            self._user_config[self.section] = {}

        self._user_config[self.section].update(updates)

        self._save_user_section()
        self.merged_section = self._merge_section()
    
    def delete_key_from_config(self, key: str) -> bool:
        """Deletes a key from the user config's section and writes it back."""
        if self.section in self._user_config and key in self._user_config[self.section]:
            del self._user_config[self.section][key]
            self._save_user_section()
            self.merged_section = self._merge_section()
            return True
        return False
    
    def _load_config(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        return {}

    def _merge_section(self) -> dict:
        user_section = self._user_config.get(self.section, {})
        admin_section = self._admin_config.get(self.section, {})
        return {**admin_section, **user_section}

    def _save_user_section(self):
        with open(self._user_config_path, "w") as f:
            yaml.dump(self._user_config, f, default_flow_style=False, sort_keys=False)


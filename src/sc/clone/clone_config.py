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

from pathlib import Path

from sc.config_manager import ConfigManager, MergePolicy

from .project_list.project_list_manager import ProjectListSource


class CloneConfigManager:
    """Clone-specific configuration composed over the generic config manager."""

    def __init__(self, config_manager: ConfigManager | None = None):
        self._config_manager = config_manager or ConfigManager(
            "clone",
            merge_policy={"project_lists": MergePolicy.PREFER_ADMIN},
        )

    @property
    def project_list_dir(self) -> Path:
        """Directory used to cache downloaded project-list files."""
        return self._config_manager.config_path.parent / "project_lists"

    def get_project_lists(self) -> dict:
        """Return project-list sources merged from user and admin config."""
        return self._config_manager.get_config().get("project_lists", {})

    def add_project_list(self, name: str, source: ProjectListSource) -> None:
        """Persist a project-list source in the user clone config."""
        self._config_manager.update_config(
            "project_lists",
            {name: source.model_dump(exclude_none=True)},
        )

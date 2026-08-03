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

from pydantic import BaseModel, ConfigDict, ValidationError

from sc.exceptions import ConfigError
from sc.config_manager import ConfigManager

class GitHostModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    url: str | None = None
    token: str
    provider: str

class GitHostConfig:
    def __init__(self):
        self._git_config = ConfigManager('git_instances')

    def get_patterns(self) -> set[str]:
        """Return all configured git URL patterns."""
        return self._git_config.get_config().keys()

    def get(self, url_pattern: str) -> GitHostModel:
        """Return the git config for a specific URL pattern."""
        data = self._git_config.get_config().get(url_pattern)
        if not data:
            raise ConfigError(f"Git config doesn't contain entry for {url_pattern}")
        try:
            return GitHostModel(**data)
        except ValidationError as e:
            raise ConfigError(f"Invalid config for git instance {url_pattern}: {e}")

    def write(self, pattern: str, git_config: GitHostModel):
        """Persist the config for a specific git host."""
        self._git_config.update_config({pattern: git_config.model_dump(exclude_none=True)})

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

from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from sc.config_manager import ConfigManager

class TicketHostCfg(BaseModel):
    model_config = ConfigDict(extra='forbid')

    url: str
    provider: str
    api_key: str
    username: str | None = None
    auth_type: Literal["token", "basic"] = "token"
    project_prefix: str | None = None
    description: str | None = None
    cert: str | None = None

class GitInstanceCfg(BaseModel):
    model_config = ConfigDict(extra='forbid')

    url: str | None = None
    token: str
    provider: str

class ReviewConfig:
    def __init__(self):
        self._ticket_config = ConfigManager('ticketing_instances')
        self._git_config = ConfigManager('git_instances')

    def get_ticketing_config(self) -> dict[str, TicketHostCfg]:
        return {k: TicketHostCfg(**v) for k,v in self._ticket_config.get_config().items()}

    def get_ticket_host_ids(self) -> set[str]:
        return self._ticket_config.get_config().keys()

    def get_ticket_host_data(self, identifier: str) -> TicketHostCfg:
        data = self._ticket_config.get_config().get(identifier)
        if not data:
            raise KeyError(f"Ticket instance config doesn't contain entry for {identifier}")
        try:
            return TicketHostCfg(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid config for {identifier}: {e}")

    def write_ticketing_data(self, branch_prefix: str, ticket_data: TicketHostCfg):
        self._ticket_config.update_config({branch_prefix: ticket_data.model_dump(exclude_none=True)})

    def get_git_patterns(self) -> set[str]:
        return self._git_config.get_config().keys()

    def get_git_data(self, url_pattern: str) -> GitInstanceCfg:
        data = self._git_config.get_config().get(url_pattern)
        if not data:
            raise KeyError(f"Git config doesn't contain entry for {url_pattern}")
        try:
            return GitInstanceCfg(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid config for {url_pattern}: {e}")

    def write_git_data(self, pattern: str, git_config: GitInstanceCfg):
        self._git_config.update_config({pattern: git_config.model_dump(exclude_none=True)})

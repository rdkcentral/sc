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

from .instances import GithubInstance, GitlabInstance
from .git_instance import GitInstance

class GitFactory:
    _registry = {
        "github": GithubInstance,
        "gitlab": GitlabInstance
    }

    @classmethod
    def types(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def create(cls, name: str, token: str, base_url: str | None) -> GitInstance:
        try:
            return cls._registry[name.lower()](token=token, base_url=base_url)
        except KeyError:
            raise ValueError(f"Provider name {name} doesn't match any VCS instance!")

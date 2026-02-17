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

from dataclasses import dataclass
from enum import Enum

# This is exactly StrEnum which was released in Py3.11 but we are supporting 3.10+
class BranchType(str, Enum):
    FEATURE = "feature"
    RELEASE = "release"
    SUPPORT = "support"
    HOTFIX = "hotfix"
    DEVELOP = "develop"
    MASTER = "master"

    def __str__(self):
        return self.value

@dataclass
class Branch:
    type: BranchType
    suffix: str = None

    def __post_init__(self):
        if not self.suffix and not self._is_primary_branch:
            raise ValueError("Can't create non primary branch with no suffix.")

    @property
    def name(self) -> str:
        if self.suffix:
            return f"{self.type}/{self.suffix}"
        return str(self.type)

    def _is_primary_branch(self) -> bool:
        return self.type in {BranchType.DEVELOP, BranchType.MASTER}

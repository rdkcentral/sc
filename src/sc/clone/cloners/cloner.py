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

from abc import ABC, abstractmethod
from enum import Enum
import logging
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

class RefType(Enum):
    BRANCH = "BRANCH"
    TAG = "TAG"
    SHA = "SHA"

class Cloner(ABC):
    @abstractmethod
    def clone(self, directory: Path):
        pass

    def _is_branch_tag_or_sha(self, repo_uri: str, ref: str):
        refs = subprocess.run(
            ["git", "ls-remote", repo_uri], capture_output=True, text=True).stdout

        if f"refs/heads/{ref}" in refs:
            return RefType.BRANCH
        elif f"refs/tags/{ref}" in refs:
            return RefType.TAG
        else:
            return RefType.SHA

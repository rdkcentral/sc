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

from git import Repo

from ..models import RepoInfo
from .repo_source import RepoSource

class SingleRepoSource(RepoSource):
    def __init__(self, top_dir: Path):
        self._top_dir = top_dir

    @property
    def active_branch(self) -> str:
        return Repo(self._top_dir).active_branch.name

    def get_repos(self) -> list[RepoInfo]:
        return [self._get_repo_info(Repo(self._top_dir))]

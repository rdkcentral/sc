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

from git import Repo

from ..models import RepoInfo

class RepoSource(ABC):
    @property
    @abstractmethod
    def active_branch(self) -> str:
        pass

    @abstractmethod
    def get_repos(self) -> list[RepoInfo]:
        pass

    def _get_repo_info(self, repo: Repo) -> RepoInfo:
        commit = repo.head.commit

        return RepoInfo(
            branch=repo.active_branch.name,
            directory=repo.working_dir,
            remote_url=repo.remotes[0].url,
            commit_sha=commit.hexsha[:10],
            commit_author=f"{commit.author.name} <{commit.author.email}>",
            commit_date=commit.committed_datetime,
            commit_message=commit.message.strip()
        )

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
import logging

from git import Repo
from git.exc import GitCommandError

from ..branch import BranchType
from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class List(Command):
    """List branches by branch type."""
    branch_type: BranchType

    def run_git_command(self):
        repo = Repo(self.top_dir)
        self._list_branches(repo)

    def run_repo_command(self):
        repo = Repo(self.top_dir / '.repo' / 'manifests')
        self._list_branches(repo)

    def _list_branches(self, repo: Repo):
        local_branches = self._get_local_branches(repo)
        remote_branches = [
            b for b in self._get_remote_branches(repo) if b not in local_branches]

        logger.info(f"Local {self.branch_type} branches: \n" + "\n".join(local_branches))
        logger.info(f"Remote {self.branch_type} branches: \n" + "\n".join(remote_branches))

    def _get_local_branches(self, repo: Repo):
        return [
            b.name.removeprefix(f"{self.branch_type}/")
            for b in repo.branches
            if b.name.startswith(self.branch_type)
        ]

    def _get_remote_branches(self, repo: Repo):
        remote_branches = []
        for rem in repo.remotes:
            try:
                refs = [ref.split('\t')[1] for ref in repo.git.ls_remote(rem.url).split('\n')]
            except GitCommandError:
                logger.warning(f"Failed getting branches from remote {rem.url}")
                continue
            remote_branches.extend([
                ref.removeprefix(f"refs/heads/{self.branch_type}/")
                for ref in refs
                if ref.startswith(f"refs/heads/{self.branch_type}/")
            ])
        return remote_branches

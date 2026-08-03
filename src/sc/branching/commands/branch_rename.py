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
from enum import Enum, auto
import logging
from pathlib import Path

import git
from git import Repo

from .command import Command
from sc.exceptions import ScError
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

@dataclass
class BranchRename(Command):
    old_branch: str
    new_branch: str
    local_only: bool
    git_only: bool

    def run_git_command(self):
        self._rename_repo(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")

        if self.git_only:
            self._rename_repo(Path.cwd())
            return

        for proj in manifest.projects:
            if proj.lock_status is None:
                logger.info(f"Renaming local branch in repo: {self.top_dir / proj.path}")
                self._rename_repo(self.top_dir / proj.path)

        logger.info(f"Renaming local manifest branch: {self.top_dir / '.repo' / 'manifests'}")
        self._rename_repo(self.top_dir / ".repo" / "manifests")

    def _rename_repo(self, directory: Path):
        try:
            repo = Repo(directory)
        except git.InvalidGitRepositoryError as e:
            # We should hopefully never get here. Only if the user is missing repositories
            # that should be present from their manifest.
            logger.warning(f"Skipping renaming for {directory}: Not a valid git repository.")
            return

        try:
            self._rename_local(repo)
        except ScError as e:
            logger.warning(f"Skipping renaming for {directory}: {e}")
            return

        if not self.local_only:
            try:
                self._rename_remote(repo)
            except ScError as e:
                logger.warning(f"Skipping remote renaming for {directory}: {e}")

    def _rename_local(self, repo: Repo):
        try:
            repo.git.branch("-m", self.old_branch, self.new_branch)
            logger.info("Renamed locally.")
        except git.GitCommandError as e:
            raise ScError(
                f"Unable to rename branch in repo {repo.working_dir}: {e.stderr}"
            ) from e

    def _rename_remote(self, repo: Repo):
        try:
            remote = repo.remotes[0].name
        except IndexError as e:
            raise ScError(f"No remote found for repo {repo.working_dir}.") from e

        try:
            # Push/create the new branch before deleting the old branch.
            repo.git.push("-u", remote, f"{self.new_branch}:refs/heads/{self.new_branch}")
        except git.GitCommandError as e:
            raise ScError(
                f"Failed to push new branch to remote {self.new_branch}: {e.stderr}") from e

        if self._has_remote_branch(repo, remote, self.old_branch) is not None:
            try:
                repo.git.push(remote, "--delete", self.old_branch)
            except git.GitCommandError as e:
                raise ScError(
                    f"Failed to delete old branch on remote {self.old_branch}: {e.stderr}") from e

        logger.info("Renamed remotely.")

    def _has_remote_branch(self, repo: Repo, remote_name: str, branch_name: str) -> bool:
        out = repo.git.ls_remote("--heads", remote_name, f"refs/heads/{branch_name}")

        for line in out.splitlines():
            commit, ref = line.split()
            if ref == f"refs/heads/{branch_name}":
                return True

        return False

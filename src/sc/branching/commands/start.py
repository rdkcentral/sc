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
import sys

from git import Repo

from ..branch import Branch
from .command import Command
from . import common
from git_flow_library import GitFlowLibrary
from .init import Init
from .pull import Pull
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

@dataclass
class Start(Command):
    branch: Branch
    base: str | None

    def run_git_command(self):
        Init(self.top_dir).run_git_command()
        GitFlowLibrary.start(self.top_dir, self.branch.type, self.branch.suffix, self.base)

    def run_repo_command(self):
        self._error_on_sc_uninitialised()

        manifest_dir = self.top_dir / '.repo' / 'manifests'

        manifest_repo = Repo(manifest_dir)
        self._error_if_branch_exists(manifest_repo)

        if '/' in self.base:
            base_branch_type, base_name = self.base.split('/', 1)
        else:
            base_branch_type, base_name = self.base, None

        Pull(self.top_dir, Branch(base_branch_type, base_name)).run_repo_command()

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')

        for project in manifest.projects:
            if project.lock_status is not None:
                continue

            project_repo = Repo(self.top_dir / project.path)
            project_repo.git.checkout(
                '-b', common.resolve_project_branch_name(self.branch, project))

        manifest_repo.git.checkout('-b', self.branch.name)
        manifest_repo.git.commit("--allow-empty", m=f"Starting {self.branch.name}")
        manifest_repo.git.push("-u", "origin", self.branch.name)

    def _error_if_branch_exists(self, manifest_repo: Repo):
        remote_branches = [ref.name for ref in manifest_repo.remotes['origin'].refs]
        local_branches = [head.name for head in manifest_repo.heads]
        if f"origin/{self.branch.name}" in remote_branches:
            logger.error(
                f"Branch {self.branch.name} exists on the remote manifest repo "
                "so cannot be started."
            )
            sys.exit(1)
        elif self.branch.name in local_branches:
            logger.error(
                f"Branch {self.branch.name} already exists locally in the manifest "
                "repo so cannot be started.")
            sys.exit(1)
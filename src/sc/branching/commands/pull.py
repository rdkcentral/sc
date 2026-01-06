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

from git import GitCommandError, Repo

from ..branch import Branch
from .command import Command
from . import common
from .init import Init
from repo_library import RepoLibrary
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

@dataclass
class Pull(Command):
    branch: Branch

    def run_git_command(self):
        repo = Repo(self.top_dir)
        remote = repo.remotes[0]
        remote.pull(self.branch.name)

    def run_repo_command(self):
        self._error_on_sc_uninitialised()

        manifests_repo = Repo(self.top_dir / '.repo' / 'manifests')

        manifests_repo.git.fetch()
        try:
            manifests_repo.git.checkout(self.branch.name)
        except GitCommandError:
            logger.error(f"Branch {self.branch.name} not found on manifest!")
            sys.exit(1)

        manifests_repo.remotes.origin.pull()

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')

        RepoLibrary.sync(self.top_dir, detach=True)

        Init(self.top_dir).run_repo_command()
        for project in manifest.projects:
            if project.lock_status is not None:
                continue

            project_repo = Repo(self.top_dir / project.path)
            proj_branch_name = common.resolve_project_branch_name(self.branch, project)

            local_branches = [head.name for head in project_repo.heads]
            if proj_branch_name in local_branches:
                project_repo.git.checkout(proj_branch_name)
                project_repo.git.merge(project.revision)
            else:
                project_repo.git.checkout(project.revision)
                project_repo.git.checkout('-b', proj_branch_name)

            remote_branch = f"{project.remote}/{proj_branch_name}"
            if remote_branch in [project_repo.remotes[project.remote].refs]:
                project_repo.git.branch('-u', remote_branch, proj_branch_name)

            project_repo.git.lfs('fetch')
            project_repo.git.lfs('checkout')

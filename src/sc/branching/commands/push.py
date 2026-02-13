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
import subprocess

from git import GitCommandError, Repo

from . import common
from ..branch import Branch
from .checkout import Checkout
from .command import Command
from repo_library import RepoLibrary
from sc_manifest_parser import ProjectElementInterface, ScManifest

logger = logging.getLogger(__name__)

@dataclass
class Push(Command):
    branch: Branch

    def run_git_command(self):
        repo = Repo(self.top_dir)
        remote = repo.remotes[0].name
        repo.git.push("-u", remote, self.branch.name)

    def run_repo_command(self):
        self._error_on_sc_uninitialised()

        orig_manifest_branch = RepoLibrary.get_manifest_branch(self.top_dir)

        logger.info(f"Pushing branch {self.branch.name}")
        msg = self._input_commit_msg()

        try:
            if RepoLibrary.get_manifest_branch(self.top_dir) != self.branch.name:
                Checkout(self.top_dir, self.branch)
            self._switch_manifest_to_branch(self.branch.name)
            manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
            self._push_projects(manifest.projects)
            self._update_manifest_revisions(manifest)
            self._push_manifest(msg)
        finally:
            if RepoLibrary.get_manifest_branch(self.top_dir) != orig_manifest_branch:
                Checkout(self.top_dir, orig_manifest_branch)

        logger.info(f"Push {self.branch.name} completed!")

    def _input_commit_msg(self):
        while True:
            msg = input("Input commit message for manifest: ")
            if msg:
                return msg
            logger.warning("Cannot provide an empty commit message!")

    def _push_projects(self, projects: list[ProjectElementInterface]):
        for project in projects:
            logger.info(f"Operating on {self.top_dir}/{project.path}")
            if project.lock_status == "TAG_ONLY":
                logger.info("Lock status TAG_ONLY, pushing only tags.")
                self._do_push_tag_only_project(project)
                continue

            if not self._can_push_project(project):
                continue

            self._do_push_project(project)

    def _can_push_project(self, proj: ProjectElementInterface) -> bool:
        if proj.lock_status == "READ_ONLY":
            logger.info(f"Project lock status: {proj.lock_status}. Skipping.")
            return False
        proj_repo = Repo(self.top_dir / proj.path)
        proj_branch_name = common.resolve_project_branch_name(self.branch, proj)
        if not self._local_branch_exists(proj_repo, proj_branch_name):
            logger.info("Branch doesn't exist in project. Skipping.")
            return False
        if self._remote_branch_contains(proj_repo, proj.remote, proj_branch_name):
            logger.info("Remote already contains commit. Skipping.")
            return False
        return True

    def _do_push_project(self, proj: ProjectElementInterface):
        proj_repo = Repo(self.top_dir / proj.path)
        proj_branch_name = common.resolve_project_branch_name(self.branch, proj)
        subprocess.run(
            ["git", "push", "-u", proj.remote, proj_branch_name],
            cwd=proj_repo.working_dir
        )
        subprocess.run(["git", "push", proj.remote, "--tags"], cwd=proj_repo.working_dir)

    def _do_push_tag_only_project(self, proj: ProjectElementInterface):
        proj_repo = Repo(self.top_dir / proj.path)
        subprocess.run(["git", "push", proj.remote, "--tags"], cwd=proj_repo.working_dir)

    def _local_branch_exists(self, repo: Repo, branch: str) -> bool:
        return branch in [h.name for h in repo.heads]

    def _remote_branch_contains(self, repo: Repo, remote: str, branch: str) -> bool:
        local_commit = repo.heads[branch].commit
        remote_commit = repo.refs[f"{remote}/{branch}"]
        return repo.is_ancestor(local_commit, remote_commit)

    def _update_manifest_revisions(self, manifest: ScManifest):
        for proj in manifest.projects:
            proj_repo = Repo(self.top_dir / proj.path)
            proj.revision = proj_repo.head.commit.hexsha
        manifest.write()

    def _push_manifest(self, msg: str):
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests')
        manifest_repo.git.add(A=True)
        if manifest_repo.is_dirty():
            manifest_repo.git.commit("-m", msg)
        manifest_repo.git.push("-u", "origin", self.branch.name)
        manifest_repo.git.push("origin", "--tags")

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
import sys

from git import Repo
from repo_library import RepoLibrary
from sc_manifest_parser import ProjectElementInterface, ScManifest

from . import common
from ..branch import Branch, BranchType
from .checkout import Checkout
from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class Push(Command):
    branch: Branch

    # Repo only
    message: str | None

    def run_git_command(self):
        repo = Repo(self.top_dir)
        remote = repo.remotes[0].name
        repo.git.push("-u", remote, self.branch.name)

    def run_repo_command(self):
        self._error_on_sc_uninitialised()

        orig_manifest_branch = self._get_original_branch()

        logger.info(f"Pushing branch {self.branch.name}")

        try:
            if RepoLibrary.get_manifest_branch(self.top_dir) != self.branch.name:
                Checkout(self.top_dir, self.branch).run_repo_command()

            manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
            try:
                common.validate_project_repos(self.top_dir, manifest)
            except RuntimeError as e:
                logger.error(e)
                sys.exit(1)

            self._push_projects(manifest.projects)
            self._update_manifest_revisions(manifest)
            self._push_manifest()
        finally:
            if RepoLibrary.get_manifest_branch(self.top_dir) != orig_manifest_branch.name:
                Checkout(self.top_dir, orig_manifest_branch).run_repo_command()

        logger.info(f"Push {self.branch.name} completed!")

    def _get_original_branch(self) -> Branch:
        orig_manifest_branch = RepoLibrary.get_manifest_branch(self.top_dir)

        if orig_manifest_branch == "develop":
            return Branch(BranchType.DEVELOP)
        elif orig_manifest_branch == "master":
            return Branch(BranchType.MASTER)

        if "/" in orig_manifest_branch:
            prefix, name = orig_manifest_branch.split("/", 1)
            if BranchType.is_valid(prefix):
                return Branch(BranchType(prefix), name)

        logger.error(
            f"Original manifest branch {orig_manifest_branch} is not a "
            "valid sc branch. Please checkout a valid sc branch to push."
        )
        sys.exit(1)

    def _push_projects(self, projects: list[ProjectElementInterface]):
        for project in projects:
            logger.info(f"Operating on {self.top_dir}/{project.path}")
            if project.lock_status == "TAG_ONLY":
                logger.info("Lock status TAG_ONLY, pushing only tags.")
                self._do_push_tag_only_project(project)
                continue

            if self._can_push_project(project):
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
        if self._remote_contains_commit(proj_repo, proj.remote):
            logger.info("Remote already contains commit. Skipping.")
            return False
        return True

    def _do_push_project(self, proj: ProjectElementInterface):
        proj_repo = Repo(self.top_dir / proj.path)
        proj_branch_name = common.resolve_project_branch_name(self.branch, proj)
        try:
            subprocess.run(
                ["git", "push", "-u", proj.remote, proj_branch_name],
                cwd=proj_repo.working_dir,
                check=True
            )
            subprocess.run(
                ["git", "push", proj.remote, "--tags"],
                cwd=proj_repo.working_dir,
                check=True
            )
        except subprocess.CalledProcessError:
            logger.error(
                f"Failed to push project {proj_repo.working_dir}. Resolve error and "
                "rerun."
            )
            sys.exit(1)

    def _do_push_tag_only_project(self, proj: ProjectElementInterface):
        proj_repo = Repo(self.top_dir / proj.path)
        subprocess.run(["git", "push", proj.remote, "--tags"], cwd=proj_repo.working_dir)

    def _local_branch_exists(self, repo: Repo, branch: str) -> bool:
        return branch in [h.name for h in repo.heads]

    def _remote_contains_commit(self, repo: Repo, remote: str) -> bool:
        """Any branch on remote contains current latest commit."""
        output = repo.git.branch("-r", "--contains", repo.active_branch.commit.hexsha)

        return any(line.strip().startswith(f"{remote}/")
                   for line in output.splitlines())

    def _update_manifest_revisions(self, manifest: ScManifest):
        for proj in manifest.projects:
            proj_repo = Repo(self.top_dir / proj.path)
            proj.revision = proj_repo.head.commit.hexsha
        manifest.write()

    def _push_manifest(self):
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests')
        manifest_repo.git.add(A=True)
        if manifest_repo.is_dirty():
            commit_command = ["git", "commit"]
            if self.message:
                commit_command.extend(["-m", self.message])
            try:
                subprocess.run(
                    commit_command,
                    cwd=self.top_dir / ".repo" / "manifests",
                    check=True
                )
            except subprocess.CalledProcessError:
                logger.error(
                    "Failed to commit manifest. Please check error and rerun "
                    "push."
                )
                sys.exit(1)
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", self.branch.name],
                cwd=self.top_dir / ".repo" / "manifests",
                check=True
            )
            subprocess.run(
                ["git", "push", "origin", "--tags"],
                cwd=self.top_dir / ".repo" / "manifests",
                check=True
            )
        except subprocess.CalledProcessError:
            logger.error("Failed to push manifest! Resolve errors and push again.")
            sys.exit(1)

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
import os
from pathlib import Path
import subprocess
import sys

from git import GitCommandError, Repo
from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary
from sc_manifest_parser import ScManifest

from . import common
from ..branch import Branch, BranchType
from .command import Command
from .checkout import Checkout

logger = logging.getLogger(__name__)

@dataclass
class Finish(Command):
    branch: Branch
    # Hotfix only
    base: str | None = None

    def __post_init__(self):
        self._tag_msg: str | None = None

    def run_git_command(self):
        """Runs gitflow finish in the git project.
        """
        if self.branch.type == BranchType.HOTFIX:
            base = self._resolve_base(self.top_dir)
            if not base:
                logger.error(
                    "Base required in command or config for hotfix branches. "
                    "Please use `sc hotfix finish <branch_name> <base>"
                )
                sys.exit(1)
            GitFlowLibrary.set_branch_base(self.branch.name, base, self.top_dir)
        else:
            base = None

        if self.branch.type in (BranchType.HOTFIX, BranchType.RELEASE):
            self._tag_msg = self._prompt_tag_msg()

        try:
            GitFlowLibrary.finish(
                self.top_dir,
                self.branch.type,
                name=self.branch.suffix,
                tag_message=self._tag_msg
            )
        except subprocess.CalledProcessError:
            logger.error("Git flow finish failed!")
            sys.exit(1)

    def run_repo_command(self):
        """
        Finish all projects defined in the manifest using git-flow semantics.

        Process:
        1. For each project listed in the manifest, run `git flow finish`.
        - If merge conflicts occur, they must be resolved manually before continuing.

        2. After all projects are finished, run `git flow finish` on the manifest repository.
        - If a merge conflict occurs in the manifest and the only differences are
            project revision changes, the conflict is auto-resolved.
        - This is safe because any functional conflicts between those revisions
            were already resolved when finishing the individual projects.

        3. Once the manifest is merged, pull all projects to update them to the
        latest revisions referenced by the manifest.

        4. Create an additional commit on the target branch of the manifest to
        update all project revision references to their latest state.

        Result:
        All projects and the manifest are merged consistently, and the manifest
        reflects the final resolved revisions of every project.
        """
        self._error_on_sc_uninitialised()

        if not self._branch_exists_locally_in_manifest(self.branch.name):
            logger.error(
                f"Branch {self.branch.name} doesn't exist so can't be finished!")
            sys.exit(1)

        if self.branch.type == BranchType.HOTFIX:
            base = self._resolve_base(self.top_dir / '.repo' / 'manifests')
            if not base:
                logger.error(
                    "Base required in command or config for hotfix branches."
                    "Please use `sc hotfix finish <branch_name> <base>"
                )
                sys.exit(1)
        else:
            base = None

        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")
        try:
            common.validate_project_repos(self.top_dir, manifest)
            self._require_clean_working_tree(manifest)
        except RuntimeError as e:
            logger.error(e)
            sys.exit(1)

        if RepoLibrary.get_manifest_branch(self.top_dir) != self.branch.name:
            Checkout(self.top_dir, self.branch).run_repo_command()

        if self.branch.type in {BranchType.HOTFIX, BranchType.RELEASE}:
            self._tag_msg = self._prompt_tag_msg()

        self._stop_commit_msg_popup()
        self._finish_all_projects(base)
        self._finish_manifest_repo(base)

        self._rebase_manifest(base)
        self._print_next_steps(base)

    def _resolve_base(self, path: Path) -> str:
        return self.base or GitFlowLibrary.get_branch_base(self.branch.name, path)

    def _branch_exists_locally_in_manifest(self, branch: str) -> bool:
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests')
        local_branches = [head.name for head in manifest_repo.heads]
        return branch in local_branches or branch == RepoLibrary.get_manifest_branch(self.top_dir)

    def _branch_exists(
            self, branch: str, directory: str | Path, remote: str = "origin") -> bool:
        repo = Repo(directory)
        if branch not in [h.name for h in repo.heads]:
            try:
                repo.git.fetch(remote, f"{branch}:{branch}")
            except GitCommandError:
                logger.error(f"Base branch {branch} not found on remote or locally.")
                return False
        return True

    def _require_clean_working_tree(self, manifest: ScManifest):
        """Error if a project or the manifest has a dirty working tree."""
        paths = [self.top_dir / p.path for p in manifest.projects]
        paths.append(self.top_dir / '.repo' / 'manifests')

        error = False
        for path in paths:
            proj_repo = Repo(path)

            if proj_repo.index.diff(None):
                logger.error(
                    f"{path} working tree contains unstaged changes!")
                error = True
            if proj_repo.index.diff("HEAD"):
                logger.error(
                    f"{path} working tree contains uncommitted changes!")
                error = True

        if error:
            raise RuntimeError("Projects require clean working trees!")

    def _prompt_tag_msg(self) -> str:
        while True:
            msg = input("Input tag message: ")
            if msg:
                return msg
            logger.warning("Cannot provide an empty tag message!")

    def _stop_commit_msg_popup(self):
        """Stops every merge confirming commit message."""
        os.environ["GIT_MERGE_AUTOEDIT"] = "no"

    def _finish_all_projects(self, base: str | None):
        """Run gitflow finish in all non-locked projects.

        Args:
            base (str | None): Sets the base for each project if provided.
        """
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            proj_dir = self.top_dir / proj.path
            logger.info(f"Operating on {proj_dir}")
            proj_repo = Repo(proj_dir)

            if proj.lock_status == "READ_ONLY":
                continue

            self._delete_tag_if_exists(proj_repo, self.branch.suffix)
            if proj.lock_status == "TAG_ONLY":
                logger.info(f"Project {proj_dir} is TAG_ONLY")
                if self.branch.type in {BranchType.HOTFIX, BranchType.RELEASE}:
                    proj_repo.git.tag(self.branch.suffix)
                continue

            if base:
                self._set_branch_base(base, proj_dir, proj.remote)

            try:
                GitFlowLibrary.finish(
                    proj_dir,
                    self.branch.type,
                    name=self.branch.suffix,
                    keep=True,
                    tag_message=self._tag_msg
                )
            except subprocess.CalledProcessError:
                logger.error(
                    f"Finish failed in {proj_dir}, resolve errors and rerun "
                    f"`sc {self.branch.type} finish {self.branch.suffix}`"
                )
                sys.exit(1)

    def _set_branch_base(self, base: str, directory: str | Path, remote: str = "origin"):
        if not self._branch_exists(base, directory, remote):
            logger.error(
                f"Base branch '{base}' not found locally or on remote '{remote}' "
                f"in {directory}."
            )
            sys.exit(1)
        GitFlowLibrary.set_branch_base(self.branch.name, base, directory)

    def _delete_tag_if_exists(self, repo: Repo, tag: str):
        try:
            repo.git.tag('-d', tag)
            logger.info(f"Deleted preexisting tag {tag}")
        except GitCommandError:
            pass

    def _finish_manifest_repo(self, base: str | None):
        """Run gitflow finish on the manifest repository.

        Args:
            base (str | None): Set the base branch if provided.
        """
        manifest_dir = self.top_dir / ".repo" / "manifests"
        if base:
            self._set_branch_base(base, manifest_dir)

        self._delete_tag_if_exists(Repo(manifest_dir), self.branch.suffix)
        rev_only_change_branches = self._get_branches_with_revision_only_diff(base)

        try:
            GitFlowLibrary.finish(
                manifest_dir,
                self.branch.type,
                name=self.branch.suffix,
                keep=True,
                tag_message=self._tag_msg
            )
        except subprocess.CalledProcessError:
            logger.warning(
                "Manifest finish failed. Attempting to auto resolve conflicts.")

            self._auto_resolve_manifest_conflicts(rev_only_change_branches)

    def _rebase_manifest(self, base: str | None):
        """Rewrites the manifest with any newer commits pulled on top.

        Args:
            base (str | None): The base a hotfix branch should be merged into.
        """
        if self.branch.type == BranchType.FEATURE:
            self._rebase_develop()

        elif self.branch.type == BranchType.RELEASE:
            self._rebase_master()
            self._rebase_develop()

        elif self.branch.type == BranchType.HOTFIX:
            self._rebase_base(base)

    def _rebase_develop(self):
        Repo(self.top_dir / '.repo' / 'manifests').git.switch('develop')
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status is None:
                develop = GitFlowLibrary.get_develop_branch(self.top_dir / proj.path)
                self._rebase_proj(self.top_dir / proj.path, develop)

        self._update_manifest(manifest)
        self._commit_manifest("develop")

    def _rebase_master(self):
        Repo(self.top_dir / '.repo' / 'manifests').git.switch('master')
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status is None:
                master = GitFlowLibrary.get_master_branch(self.top_dir / proj.path)
                self._rebase_proj(self.top_dir / proj.path, master)

        self._update_manifest(manifest)
        self._commit_manifest("master")

    def _rebase_base(self, base: str | None):
        Repo(self.top_dir / '.repo' / 'manifests').git.switch(base)
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status is None:
                self._rebase_proj(self.top_dir / proj.path, base)

        self._update_manifest(manifest)
        self._commit_manifest(base)

    def _rebase_proj(self, proj_path: Path, branch: str):
        proj_repo = Repo(proj_path)
        proj_repo.git.switch(branch)
        try:
            subprocess.run(["git", "pull"], cwd=proj_path, check=True)
        except subprocess.CalledProcessError:
            logger.error(
                f"Rebase failed in {proj_path}, please resolve above error and rerun "
                f"`sc {self.branch.type} finish {self.branch.suffix}`"
            )
            sys.exit(1)

    def _update_manifest(self, manifest: ScManifest):
        for proj in manifest.projects:
            if proj.lock_status is None:
                proj_repo = Repo(self.top_dir / proj.path)
                proj.revision = proj_repo.head.commit.hexsha

        manifest.write()

    def _commit_manifest(self, branch: str):
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests')
        manifest_repo.git.add(A=True)
        manifest_repo.git.commit(
            '--allow-empty',
            '-m',
            f"Finished {self.branch.name}. Rebase {branch}")

    def _print_next_steps(self, base: str):
        logger.info("Finish completed!")
        if self.branch.type == BranchType.RELEASE:
            logger.info("Run sc develop push and sc master push to push to remote!")
        elif self.branch.type == BranchType.FEATURE:
            logger.info("Run sc develop push to push to remote!")
        elif self.branch.type == BranchType.HOTFIX:
            if "/" in base:
                base_prefix, base_name = base.split('/', 1)
            else:
                base_prefix = base
            logger.info(f"Run sc {base_prefix} push to push to remote!")

    def _auto_resolve_manifest_conflicts(
            self,
            rev_only_change_branches: list[str]
    ):
        """
        Resolve manifest merge conflict automatically if only project revisions have
        changed between them.

        Args:
            rev_only_change_branches (list[str]): A list of target branches that have
                changes in only the revisions.
        """
        manifest_repo = Repo(self.top_dir / ".repo" / 'manifests')
        while True:
            if not self._has_merge_conflicts(manifest_repo):
                logger.error(
                    "Finish failed but no merge conflicts were detected in the manifest "
                    "repository. Manual intervention required."
                )
                sys.exit(1)

            if manifest_repo.active_branch.name not in rev_only_change_branches:
                logger.error(
                    "Can't automatically resolve conflict! Resolve yourself and "
                    f"rerun `sc {self.branch.type} finish {self.branch.suffix}`"
                )
                sys.exit(1)

            rev_only_change_branches.remove(manifest_repo.active_branch.name)

            for path in manifest_repo.index.unmerged_blobs().keys():
                manifest_repo.git.checkout("--ours", path)
            manifest_repo.git.commit("-am", "Automatic conflict resolution.")

            try:
                GitFlowLibrary.finish(
                    manifest_repo.working_dir,
                    self.branch.type,
                    name=self.branch.suffix,
                    keep=True,
                    tag_message=self._tag_msg
                )
                # Break on successful finish.
                break
            except subprocess.CalledProcessError:
                # Loop to next branch or failure.
                continue

    def _get_branches_with_revision_only_diff(self, base: str | None) -> list[str]:
        """Get a list of target manifest branches that differ only by revisions.
            These branches are then able to be auto resolved if there is a conflict.

        Args:
            base (str | None): The base if finishing a hotfix branch.

        Returns:
            list[str]: A list of relevant branches which manifest differs from the
                starting manifest by revision only.

        """
        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")
        branches: list[str] = []

        def check(branch_name: str | None):
            if not branch_name:
                return
            other = self._get_branches_manifest(branch_name)
            if manifest.equals(other, ignore_attrs={"revision"}):
                branches.append(branch_name)

        match self.branch.type:
            case BranchType.RELEASE:
                check("develop")
                check("master")
            case BranchType.FEATURE:
                check("develop")
            case BranchType.HOTFIX:
                check(base)

        return branches

    def _has_merge_conflicts(self, repo: Repo):
        return bool(repo.index.unmerged_blobs())

    def _get_branches_manifest(self, branch: str) -> ScManifest:
        """Get the ScManifest of a particular branch."""
        manifest_repo = Repo(self.top_dir / ".repo" / "manifests")
        start_branch = manifest_repo.active_branch.name
        try:
            manifest_repo.git.switch(branch)
            manifest = ScManifest.from_repo_root(self.top_dir / ".repo")
        finally:
            manifest_repo.git.switch(start_branch)
        return manifest


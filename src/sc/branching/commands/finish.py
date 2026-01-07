from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess
import sys

from git import GitCommandError, Repo

from ..branch import Branch, BranchType
from .command import Command
from .checkout import Checkout
from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

class FinishOperationError(RuntimeError):
    def __init__(self, path: str | Path, message: str):
        super().__init__(
            f"Finish failed in {path}: {message} \n"
            "Please resolve error and rerun sc finish."
        )

@dataclass
class Finish(Command):
    branch: Branch
    # Hotfix only
    base: str | None = None

    def __post_init__(self):
        self._tag_msg: str | None = None

    def run_git_command(self):
        """Runs gitflow finish in the git project.

        Raises:
            FinishOperationError: If the project fails to finish
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
            raise FinishOperationError(self.top_dir, "Check above for error.")

    def run_repo_command(self):
        """Runs gitflow finish in all non locked manifest projects, then
        runs gitflow finish in the manifest repository and finally updates
        the manifest with the new commit shas.

        Raises:
            FinishOperationError: If any project fails to finish.
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

        if RepoLibrary.get_manifest_branch(self.top_dir) != self.branch.name:
            Checkout(self.top_dir, self.branch)

        if self.branch.type in {BranchType.HOTFIX, BranchType.RELEASE}:
            self._tag_msg = self._prompt_tag_msg()

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

    def _prompt_tag_msg(self) -> str:
        while True:
            msg = input("Input tag message: ")
            if msg:
                return msg
            logger.warning("Cannot provide an empty tag message!")

    def _finish_all_projects(self, base: str | None):
        """Run gitflow finish in all non-locked projects.

        Args:
            base (str | None): Sets the base for each project if provided.

        Raises:
            FinishOperationError: If any project fails to finish.
        """
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status is not None:
                continue
            proj_dir = self.top_dir / proj.path
            logger.info(f"Operating on {proj_dir}")
            proj_repo = Repo(proj_dir)
            if base:
                try:
                    self._set_branch_base(base, proj.path, proj.remote)
                except ValueError as e:
                    raise FinishOperationError(proj.path, e)

            self._delete_tag_if_exists(proj_repo, self.branch.suffix)
            try:
                GitFlowLibrary.finish(
                    proj_dir,
                    self.branch.type,
                    name=self.branch.suffix,
                    keep=True,
                    tag_message=self._tag_msg
                )
            except subprocess.CalledProcessError:
                raise FinishOperationError(proj.path, "Check above for error.")

    def _set_branch_base(self, base: str, directory: str | Path, remote: str = "origin"):
        if not self._branch_exists(base, directory, remote):
            raise ValueError(f"Base branch '{base}' not found locally or on {remote}.")
        GitFlowLibrary.set_branch_base(self.branch.name, base, directory)

    def _delete_tag_if_exists(self, repo: Repo, tag: str):
        try:
            logger.info(f"Attempt deleting tag: {tag}")
            repo.git.tag('-d', tag)
        except GitCommandError:
            logger.info(f"Tag doesn't exist.")

    def _finish_manifest_repo(self, base: str | None):
        """Run gitflow finish on the manifest repository.

        Args:
            base (str | None): Set the base branch if provided.
        """
        if base:
            try:
                self._set_branch_base(base, self.top_dir / '.repo' / 'manifests')
            except ValueError as e:
                raise FinishOperationError(self.top_dir / '.repo' / 'manifests', e)
        self._delete_tag_if_exists(
            Repo(self.top_dir / '.repo' / 'manifests'), self.branch.suffix)
        try:
            GitFlowLibrary.finish(
                self.top_dir / '.repo' / 'manifests',
                self.branch.type,
                name=self.branch.suffix,
                keep=True,
                tag_message=self._tag_msg
            )
        except subprocess.CalledProcessError:
            raise FinishOperationError(
                self.top_dir / '.repo' / 'manifests', "Check above for error.")

    def _rebase_manifest(self, base: str | None):
        """R

        Args:
            base (str | None): _description_
        """
        if self.branch.type == BranchType.FEATURE:
            self._rebase_to_develop()

        elif self.branch.type == BranchType.RELEASE:
            self._rebase_to_master()
            self._rebase_to_develop()

        elif self.branch.type == BranchType.HOTFIX:
            self._rebase_to_base(base)

    def _rebase_to_develop(self):
        Repo(self.top_dir / '.repo' / 'manifests').git.switch('develop')
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status is None:
                develop = GitFlowLibrary.get_develop_branch(self.top_dir / proj.path)
                Repo(self.top_dir / proj.path).git.switch(develop)
        self._commit_manifest("develop")

    def _rebase_to_master(self):
        Repo(self.top_dir / '.repo' / 'manifests').git.switch('master')
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status == None:
                master = GitFlowLibrary.get_master_branch(self.top_dir / proj.path)
                Repo(self.top_dir / proj.path).git.switch(master)
        self._commit_manifest("master")

    def _rebase_to_base(self, base: str | None):
        Repo(self.top_dir / '.repo' / 'manifests').git.switch(base)
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status == None:
                Repo(self.top_dir / proj.path).git.switch(base)
        self._commit_manifest(base)

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
            base_prefix, base_name = base.split('/', 1)
            logger.info(f"Run sc {base_prefix} push {base_prefix} to push to remote!")
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

class BranchState(Enum):
    RENAME_NEEDED = auto()
    ALREADY_RENAMED = auto()
    INVALID = auto()

@dataclass
class BranchRename(Command):
    old_branch: str
    new_branch: str

    def run_git_command(self):
        self._rename_branch(self.top_dir, self.old_branch, self.new_branch)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")

        for proj in manifest.projects:
            if proj.lock_status is None:
                logger.info(f"Attempting renaming branch in repo: {self.top_dir / proj.path}")
                self._rename_branch(
                    self.top_dir / proj.path,
                    self.old_branch,
                    self.new_branch,
                    proj.remote,
                )

        logger.info(f"Attempting renaming manifest branch: {self.top_dir / '.repo' / 'manifests'}")
        self._rename_branch(
            self.top_dir / ".repo" / "manifests",
            self.old_branch,
            self.new_branch,
        )

    def _rename_branch(
            self,
            directory: Path,
            old_branch: str,
            new_branch: str,
            remote_name: str | None = None):
        try:
            repo = Repo(directory)
        except git.InvalidGitRepositoryError as e:
            raise ScError(f"Invalid git repo: {directory}") from e

        branch_state = self._branch_state(repo, old_branch, new_branch)
        if branch_state is BranchState.INVALID:
            return

        try:
            remote = self._remote_name(repo, remote_name)
        except RuntimeError as e:
            logger.warning(f"{e} Skipping remote renaming.")
            remote = None

        old_remote_commit = None
        new_remote_commit = None

        if remote:
            try:
                old_remote_commit = self._remote_branch_commit(repo, remote, old_branch)
                new_remote_commit = self._remote_branch_commit(repo, remote, new_branch)
            except git.GitCommandError as e:
                logger.warning(
                    f"Unable to inspect remote {remote} in repo {repo.working_dir}. "
                    f"Skipping branch rename: {e.stderr}"
                )
                return

            local_branch = old_branch
            if branch_state is BranchState.ALREADY_RENAMED:
                local_branch = new_branch

            if self._remote_target_conflicts(
                    repo, remote, local_branch, new_branch, new_remote_commit):
                return

        if branch_state is BranchState.RENAME_NEEDED:
            self._rename_local(repo, old_branch, new_branch)

        if remote:
            create_missing_remote = (
                branch_state is BranchState.ALREADY_RENAMED
                and self._tracks_remote(repo, new_branch, remote)
            )

            self._finish_remote_rename(
                repo,
                remote,
                old_branch,
                new_branch,
                old_remote_commit,
                new_remote_commit,
                create_missing_remote,
            )

    def _branch_state(self, repo: Repo, old_branch: str, new_branch: str) -> BranchState:
        has_old = self._has_branch(repo, old_branch)
        has_new = self._has_branch(repo, new_branch)

        if has_old and not has_new:
            return BranchState.RENAME_NEEDED

        if not has_old and has_new:
            logger.info(f"Branch already renamed in repo {repo.working_dir}. Continuing.")
            return BranchState.ALREADY_RENAMED

        if has_old and has_new:
            logger.warning(
                f"Both branches exist in repo {repo.working_dir}: "
                f"{old_branch}, {new_branch}. Skipping."
            )
            return BranchState.INVALID

        logger.warning(
            f"Neither branch exists in repo {repo.working_dir}: "
            f"{old_branch}, {new_branch}. Skipping."
        )
        return BranchState.INVALID

    def _rename_local(self, repo: Repo, old_branch: str, new_branch: str):
        try:
            repo.git.branch("-m", old_branch, new_branch)
            logger.info("Renamed locally.")
        except git.GitCommandError as e:
            raise ScError(
                f"Unable to rename branch in repo {repo.working_dir}: {e.stderr}"
            ) from e

    def _finish_remote_rename(
            self,
            repo: Repo,
            remote: str,
            old_branch: str,
            new_branch: str,
            old_remote_commit: str | None,
            new_remote_commit: str | None,
            create_missing_remote: bool):
        if old_remote_commit is None and new_remote_commit is None and not create_missing_remote:
            logger.info(
                f"Remote branch {old_branch} not found in repo {repo.working_dir}. "
                "Skipping remote renaming."
            )
            return

        try:
            # Push/create the new branch before deleting the old branch.
            repo.git.push("-u", remote, f"{new_branch}:refs/heads/{new_branch}")

            if old_remote_commit is not None:
                repo.git.push(remote, "--delete", old_branch)

            logger.info("Renamed remotely.")
        except git.GitCommandError as e:
            logger.warning(
                f"Failed to rename branch in remote in repo {repo.working_dir}: "
                f"{e.stderr}"
            )

    def _remote_target_conflicts(
            self,
            repo: Repo,
            remote: str,
            local_branch: str,
            new_branch: str,
            new_remote_commit: str | None) -> bool:
        if new_remote_commit is None:
            return False

        local_commit = self._local_branch_commit(repo, local_branch)
        if local_commit == new_remote_commit:
            return False

        logger.warning(
            f"Remote branch {new_branch} already exists on {remote} in repo "
            f"{repo.working_dir} and points at a different commit. Skipping."
        )
        return True

    def _remote_name(self, repo: Repo, remote_name: str | None) -> str:
        if remote_name:
            try:
                return repo.remote(remote_name).name
            except ValueError as e:
                raise RuntimeError(
                    f"No remote named {remote_name} found for {repo.working_dir}.") from e

        try:
            return repo.remotes[0].name
        except IndexError as e:
            raise RuntimeError(f"No remote found for repo {repo.working_dir}.") from e

    def _has_branch(self, repo: Repo, branch_name: str) -> bool:
        return branch_name in [branch.name for branch in repo.branches]

    def _local_branch_commit(self, repo: Repo, branch_name: str) -> str:
        return repo.git.rev_parse(branch_name)

    def _remote_branch_commit(
            self,
            repo: Repo,
            remote_name: str,
            branch_name: str) -> str | None:
        out = repo.git.ls_remote("--heads", remote_name, f"refs/heads/{branch_name}")

        for line in out.splitlines():
            commit, ref = line.split()
            if ref == f"refs/heads/{branch_name}":
                return commit

        return None

    def _tracks_remote(self, repo: Repo, branch_name: str, remote_name: str) -> bool:
        try:
            tracking_branch = repo.heads[branch_name].tracking_branch()
        except IndexError:
            return False

        return tracking_branch is not None and tracking_branch.remote_name == remote_name
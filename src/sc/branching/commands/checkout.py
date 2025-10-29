from dataclasses import dataclass
import logging
import sys

from git import GitCommandError, Repo

from ..branch import Branch
from .command import Command
from . import common
from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

@dataclass
class Checkout(Command):
    branch: Branch
    # Repo only:
    force: bool = False
    verify: bool = False

    def run_git_command(self):
        GitFlowLibrary.checkout(self.top_dir, self.branch.type, self.branch.suffix)

    def run_repo_command(self):
        self._error_on_sc_uninitialised()

        manifests_repo = Repo(self.top_dir / '.repo' / 'manifests')
        manifests_repo.git.fetch()
        try:
            manifests_repo.git.checkout(self.branch.name)
        except GitCommandError:
            logger.error(f"Branch {self.branch.name} not found on manifest!")
            sys.exit(1)
        
        RepoLibrary.sync(
            self.top_dir,
            force_sync=self.force,
            force_checkout=self.force,
            verify=self.verify,
            detach=True,
            no_prune=True
        )
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for project in manifest.projects:
            logger.info(f"Operating on {self.top_dir/project.path}")
            if project.lock_status is not None:
                continue

            project_repo = Repo(self.top_dir / project.path)
            proj_branch_name = common.resolve_project_branch_name(self.branch, project)

            local_branches = [head.name for head in project_repo.heads]
            if proj_branch_name in local_branches:
                project_repo.git.switch(proj_branch_name)
            else:
                project_repo.git.switch('-c', proj_branch_name)
            
            remote_branch = f"{project.remote}/{proj_branch_name}"
            if remote_branch in [project_repo.remotes[project.remote].refs]:
                project_repo.git.branch('-u', remote_branch, proj_branch_name)

            project_repo.git.lfs('fetch')
            project_repo.git.lfs('checkout')

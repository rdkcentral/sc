from dataclasses import dataclass
from pathlib import Path

from git import Repo

from .command import Command
from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary
from sc_manifest_parser import ProjectElementInterface, ScManifest

@dataclass
class Init(Command):
    def run_git_command(self):
        GitFlowLibrary.init(self.top_dir)
    
    def run_repo_command(self):
        Init.init_gitflow_for_manifest(self.top_dir)

        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")
        for project in manifest.projects:
            if project.lock_status == None:
                Init.init_gitflow_for_project(self.top_dir, project)
    
    @staticmethod
    def init_gitflow_for_manifest(top_dir: Path):
        manifest_repo = Repo(top_dir / '.repo' / 'manifests')
        branch = RepoLibrary.get_manifest_branch(top_dir)
        Init._setup_gitflow_branch(
            manifest_repo,
            "master"
        )
        Init._setup_gitflow_branch(
            manifest_repo,
            "develop"
        )
        GitFlowLibrary.init(top_dir / '.repo' / 'manifests')
        manifest_repo.git.switch('-C', branch)
        remote_branch = f"origin/{branch}"
        remote_branches = [r.name for r in manifest_repo.remotes["origin"].refs]
        if remote_branch in remote_branches:
            manifest_repo.git.branch('-u', remote_branch, branch)

    @staticmethod
    def init_gitflow_for_project(top_dir: Path, project: ProjectElementInterface):
        directory = top_dir / project.path
        branch = RepoLibrary.get_manifest_branch(top_dir)
        repo = Repo(directory)
        remote = project.remote

        Init._setup_gitflow_branch(
            repo,
            "master", 
            project.alternative_master,
            remote
        )
        Init._setup_gitflow_branch(
            repo,
            "develop",
            project.alternative_develop,
            remote
        )

        GitFlowLibrary.init(directory)
        repo.git.switch('-C', branch)
        remote_branch = f"{project.remote}/{branch}"
        remote_branches = [r.name for r in repo.remotes[project.remote].refs]
        if remote_branch in remote_branches:
            print("Set tracking branch")
            repo.git.branch('-u', remote_branch, branch)
    
    @staticmethod
    def _setup_gitflow_branch(
            repo: Repo,
            default_branch: str, 
            alt_branch: str | None = None,
            remote: str = 'origin'
        ):
        """Configure git branches for use by git flow."""
        remote_branches = [ref.name for ref in repo.remotes[remote].refs]
        if alt_branch:
            branch = alt_branch
        else:
            if default_branch == "master":
                if f"{remote}/main" in remote_branches:
                    branch = "main"
                else:
                    branch = "master"
            else:
                branch = default_branch
        
        repo.git.config(f"gitflow.branch.{default_branch}", branch)
        Init._ensure_branch(repo, branch, remote)
    
    # Potentially should be moved to a more universal place if other classes need to use
    # it. Leaving here for now.
    @staticmethod
    def _ensure_branch(repo: Repo, branch: str, remote: str):
        """Ensure a branch exists, create it if not and return to starting branch.

        Args:
            repo (Repo): The repo you want to ensure the branch in.
            branch (str): The branch to ensure.
            remote (str): The remote to track.
        """        
        detached = repo.head.is_detached
        if detached:
            orig_sha = repo.head.commit.hexsha
        else:
            orig_branch = repo.active_branch.name

        remote_branches = [ref.name for ref in repo.remotes[remote].refs]
        local_branches = [head.name for head in repo.heads]

        remote_ref = f"{remote}/{branch}"
        local_exists = branch in local_branches
        remote_exists = remote_ref in remote_branches

        if local_exists:
            repo.git.checkout(branch)
            if remote_exists:
                repo.git.branch("--set-upstream-to", remote_ref, branch)
        else:
            if remote_exists:
                repo.git.checkout("-b", branch, "--track", remote_ref)
            else:
                repo.git.checkout("-b", branch)

        if detached:
            repo.git.checkout('--detach', orig_sha)
        else:
            repo.git.checkout(orig_branch)
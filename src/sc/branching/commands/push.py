from dataclasses import dataclass
import logging
import subprocess
import sys

from git import GitCommandError, Repo

from ..branch import Branch
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
            self._switch_manifest_to_branch(self.branch.name)
            manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
            self._push_projects(manifest.projects)
            self._update_manifest_revisions(manifest)
            self._push_manifest(msg)
        finally:
            self._switch_manifest_to_branch(orig_manifest_branch)

        logger.info(f"Push {self.branch.name} completed!")
    
    def _input_commit_msg(self):
        while True:
            msg = input("Input commit message for manifest: ")
            if msg:
                return msg
            logger.warning("Cannot provide an empty commit message!")

    def _switch_manifest_to_branch(self, branch: str):
        try:
            Repo(self.top_dir / '.repo' / 'manifests').git.switch(branch)
        except GitCommandError:
            logger.error(f"Branch {branch} doesn't exist on manifest!")
    
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
        if not self._local_branch_exists(proj_repo, self.branch.name):
            logger.info("Branch doesn't exist in project. Skipping.")
            return False
        if self._remote_contains(proj_repo, proj.remote, proj_repo.heads[self.branch.name].commit.hexsha):
            logger.info("Remote already contains commit. Skipping.")
            return False
        return True
    
    def _do_push_project(self, proj: ProjectElementInterface):
        proj_repo = Repo(self.top_dir / proj.path)
        subprocess.run(
            ["git", "push", "-u", proj.remote, self.branch.name], 
            cwd=proj_repo.working_dir
        )
        subprocess.run(["git", "push", "--tags"], cwd=proj_repo.working_dir)
    
    def _do_push_tag_only_project(self, proj: ProjectElementInterface):
        proj_repo = Repo(self.top_dir / proj.path)
        subprocess.run(["git", "push", "--tags"], cwd=proj_repo.working_dir)

    def _local_branch_exists(self, repo: Repo, branch: str) -> bool:
        return branch in [h.name for h in repo.heads]

    def _remote_contains(self, repo: Repo, remote: str, sha: str) -> bool:
        out = repo.git.branch("-r", "--contains", sha)
        return any(line.strip().startswith(f"{remote}/") for line in out.splitlines())

    def _update_manifest_revisions(self, manifest: ScManifest):
        for proj in manifest.projects:
            proj_repo = Repo(self.top_dir / proj.path)
            proj.revision = proj_repo.head.commit.hexsha
        manifest.write()

    def _push_manifest(self, msg: str):
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests') 
        manifest_repo.git.add(A=True)
        manifest_repo.git.commit("-m", msg)
        manifest_repo.git.push("-u", "origin", self.branch.name)

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
"""Module for `sc group` functionality."""

from dataclasses import dataclass
import logging
import subprocess
import sys

import git
from git import Repo
from sc_manifest_parser import ProjectElementInterface, ScManifest

from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class GroupShow(Command):
    """List groups or show information about a particular group."""
    group: str | None

    def run_git_command(self):
        logger.error("`sc show group` must be ran inside a repo project!")

    def run_repo_command(self):
        if self.group:
            self._show_group_info()
        else:
            self._list_groups()

    def _show_group_info(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        group_shown = False
        for proj in manifest.projects:
            if _project_in_group(proj, self.group):
                group_shown = True
                self._show_project(proj)
                print()
                logger.info("-" * 100)

        if not group_shown:
            logger.warning(f"No project matching group `{self.group}` found!")

    def _list_groups(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        groups = []
        for proj in manifest.projects:
            project_groups = proj.groups
            if project_groups:
                groups.extend(project_groups.split(","))
        for group in sorted(set(groups)):
            logger.info(f"[{group}]")

    def _show_project(self, proj: ProjectElementInterface):
        """Show information pertaining to a particular project."""
        proj_dir = self.top_dir / proj.path
        logger.info(f"Project: {proj_dir}")
        logger.info(
            f"Lock Status: [bold yellow]\[{proj.lock_status or 'NORMAL'}][/]",
            extra={"markup": True}
        )

        try:
            repo = Repo(proj_dir)
            if repo.remotes:
                remote = repo.remotes[0]
                url = next(remote.urls)
                remote_status = f"{remote.name}  {url}"
            else:
                remote_status = "No remotes configured"

            logger.info(f"Remote Status: {remote_status}")
            
            subprocess.run(
                ["git", "branch", "-vv", "--color=always"],
                cwd=proj_dir,
                check=False
            )
        except git.NoSuchPathError:
            logger.error(
                f"[bold red]Project path {proj_dir} isn't a valid directory![/]",
                extra={"markup": True})
        except git.InvalidGitRepositoryError:
            logger.error(
                f"[bold red]Project path {proj_dir} isn't a valid git repository![/]",
                extra={"markup": True})

@dataclass
class GroupTag(Command):
    """Tag all projects belonging to a group."""
    group: str
    tag: str
    message: str | None
    push: bool

    def run_git_command(self):
        logger.error("`sc group tag` must be ran inside a repo project!")
        sys.exit(1)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        failures = []
        group_found = False

        for proj in manifest.projects:
            if not _project_in_group(proj, self.group):
                continue

            group_found = True
            proj_path = self.top_dir / proj.path
            logger.info(f"Operating on: {proj_path}")
            repo = Repo(proj_path)

            try:
                if self.message:
                    repo.git.tag(self.tag, "-m", self.message)
                else:
                    repo.git.tag(self.tag)
                logger.info(f"Tagged {proj_path}")

                if self.push:
                    repo.git.push(proj.remote, self.tag)
                    logger.info("Pushed tag.")
            except git.GitCommandError as e:
                failures.append((proj.path, str(e)))

        if not group_found:
            logger.error(f"No projects match {self.group}!")

        if failures:
            logger.error("Tagging completed with errors:")
            for path, err in failures:
                logger.error(f"{path} -> {err}")
        else:
            logger.info("Tagging completed successfully.")

@dataclass
class GroupCheckout(Command):
    """Checkout a branch on all projects in a group."""
    group: str
    branch: str

    def run_git_command(self):
        logger.error("sc group checkout must be ran inside a repo project!")
        sys.exit(1)

    def run_repo_command(self):
        group_found = False

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if not _project_in_group(proj, self.group):
                continue

            group_found = True
            proj_dir = self.top_dir / proj.path
            logger.info(f"Operating on: {proj_dir}")
            try:
                Repo(proj_dir).git.checkout(self.branch)
                logger.info(f"Checked out {self.branch}")
            except git.GitCommandError as e:
                logger.error(f"Failed to checkout branch: {e}")

        if not group_found:
            logger.error(f"No projects matching group: {self.group}")

@dataclass
class GroupCmd(Command):
    """Run a command in all projects in a group."""
    group: str
    command: tuple[str]

    def run_git_command(self):
        logger.error("sc group cmd must be ran inside a repo project!")
        sys.exit(1)

    def run_repo_command(self):
        group_found = False

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if not _project_in_group(proj, self.group):
                continue

            group_found = True
            subprocess.run(
                self.command,
                cwd=proj.path,
                check=False
            )

        if not group_found:
            logger.error(f"No projects matching group: {self.group}")

@dataclass
class GroupPull(Command):
    group: str

    def run_git_command(self):
        logger.error("sc group pull must be ran inside a repo project!")
        sys.exit(1)

    def run_repo_command(self):
        group_found = False

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if not _project_in_group(proj, self.group):
                continue

            proj_dir = self.top_dir / proj.path
            logger.info(f"Operating in {proj_dir}")
            group_found = True
            try:
                Repo(proj_dir).git.pull()
                logger.info("Pulled project.")
            except git.GitCommandError as e:
                logger.error(f"Failed to pull project: {e}")

        if not group_found:
            logger.error(f"No projects matching group: {self.group}")

@dataclass
class GroupFetch(Command):
    group: str

    def run_git_command(self):
        logger.error("sc group fetch must be ran inside a repo project!")
        sys.exit(1)

    def run_repo_command(self):
        group_found = False

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if not _project_in_group(proj, self.group):
                continue

            proj_dir = self.top_dir / proj.path
            logger.info(f"Operating in {proj_dir}")
            group_found = True
            try:
                Repo(proj_dir).git.fetch()
                logger.info("Fetched project.")
            except git.GitCommandError as e:
                logger.error(f"Failed to fetch project: {e}")

        if not group_found:
            logger.error(f"No projects matching group: {self.group}")

@dataclass
class GroupPush(Command):
    group: str

    def run_git_command(self):
        logger.error("sc group push must be ran inside a repo project!")
        sys.exit(1)

    def run_repo_command(self):
        group_found = False

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if not _project_in_group(proj, self.group):
                continue

            proj_dir = self.top_dir / proj.path
            logger.info(f"Operating in {proj_dir}")
            group_found = True
            repo = Repo(proj_dir)
            try:
                repo.git.push("-u", proj.remote, repo.active_branch.name)
                logger.info("Pushed project.")
            except git.GitCommandError as e:
                logger.error(f"Failed to push project: {e}")

        if not group_found:
            logger.error(f"No projects matching group: {self.group}")

def _project_in_group(proj: ProjectElementInterface, group: str) -> bool:
    """Does a project belong to a group."""
    return proj.groups and group in proj.groups.split(",")

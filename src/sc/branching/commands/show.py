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
"""Commands to display information about a repo or sc project."""

from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess

import git
from git import Repo
from sc_manifest_parser import ProjectElementInterface, ScManifest

from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class ShowBranch(Command):
    """Show branch information for all repositories."""
    def run_git_command(self):
        self._show_branch(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            self._show_project(proj)
            print()
            logger.info("-" * 100)

    def _show_project(self, proj: ProjectElementInterface):
        """Show information pertaining to a particular project."""
        proj_dir = self.top_dir / proj.path
        logger.info(f"Project: {proj_dir}")
        logger.info(
            f"Lock Status: \[[bold yellow]{proj.lock_status or 'NORMAL'}[/]]",
            extra={"markup": True}
        )

        if proj.groups:
            groups = proj.groups.split(",")
            group_str = " ".join([f"\[[bold yellow]{g}[/]]" for g in groups])
        else:
            group_str = "\[[red bold]No Groups[/]]"

        logger.info(f"Groups: {group_str}", extra={"markup": True})

        self._show_branch(proj_dir)

    def _show_branch(self, repo_dir: Path):
        """Show remotes and branches of a git repo."""
        try:
            repo = Repo(repo_dir)
        except git.NoSuchPathError:
            logger.error(
                f"[bold red]Project path {repo_dir} is not a valid directory![/]",
                extra={"markup": True})
            return
        except git.InvalidGitRepositoryError:
            logger.warning(
                f"[bold red]Project path {repo_dir} is not a valid git repository![/]",
                extra={"markup": True})
            return

        if repo.remotes:
            remote = repo.remotes[0]
            url = next(remote.urls)
            remote_status = f"{remote.name}  {url}"
        else:
            remote_status = "No remotes configured"

        logger.info(f"Remote Status: {remote_status}")

        subprocess.run(
            ["git", "branch", "-vv", "--color=always"],
            cwd=repo_dir,
            check=False
        )

@dataclass
class ShowRepoFlowConfig(Command):
    """Show git flow config for all projects."""
    def run_git_command(self):
        logger.error("`sc show repo_flow_config` must be ran inside a repo project!")

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            proj_dir = self.top_dir / proj.path
            logger.info(f"Repo Flow Config: {proj_dir}")
            result = subprocess.run(
                ["git", "config", "--list"],
                cwd=proj_dir,
                capture_output=True,
                text=True,
                check=False
            )

            for line in result.stdout.splitlines():
                if "gitflow" in line:
                    print(line)

            print()
            logger.info("-" * 100)

@dataclass
class ShowLog(Command):
    """Display most recent commit on all repositories."""
    def run_git_command(self):
        self._show_log(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            logger.info(f"Project: {self.top_dir / proj.path}")
            self._show_log(self.top_dir / proj.path)
            logger.info("-" * 100)

    def _show_log(self, repo_dir: Path):
        subprocess.run(
            ["git", "log", "--pretty=oneline", "-n1"],
            cwd=repo_dir,
            check=False
        )

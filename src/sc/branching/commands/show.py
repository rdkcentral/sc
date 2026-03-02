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

from git import Repo
from sc_manifest_parser import ProjectElementInterface, ScManifest

from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class ShowBranch(Command):
    """Show branch information for all repositories."""
    def run_git_command(self):
        _show_branch(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            _show_project(self.top_dir, proj)
            print()
            logger.info("-" * 100)

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

def _show_project(top_dir: Path, proj: ProjectElementInterface):
    """Show information pertaining to a particular project."""
    proj_dir = top_dir / proj.path
    logger.info(f"Project: {proj_dir}")
    logger.info(
        f"Lock Status: [bold yellow]\[{proj.lock_status or 'NORMAL'}][/]",
        extra={"markup": True}
    )
    _show_branch(proj_dir)

def _show_branch(repo_dir: Path):
    """Show remotes and branches of a git repo."""
    repo = Repo(repo_dir)
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

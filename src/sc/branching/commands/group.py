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
            project_groups = proj.groups
            if not project_groups or self.group not in project_groups.split(","):
                continue

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
        groups = self._remove_duplicates(groups)
        for group in groups:
            logger.info(f"[{group}]")

    def _remove_duplicates(self, target_list: list) -> list:
        return(list(dict.fromkeys(target_list)))

    def _show_project(self, proj: ProjectElementInterface):
        """Show information pertaining to a particular project."""
        proj_dir = self.top_dir / proj.path
        logger.info(f"Project: {proj_dir}")
        logger.info(
            f"Lock Status: [bold yellow]\[{proj.lock_status or 'NORMAL'}][/]",
            extra={"markup": True}
        )

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

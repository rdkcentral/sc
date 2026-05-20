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
from pathlib import Path

from git import GitCommandError, Repo
from git_flow_library import GitFlowLibrary
from sc_manifest_parser import ScManifest

from ..branch import Branch
from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class Delete(Command):
    branch: Branch
    remote: bool = False

    def run_git_command(self):
        self._delete_branch(self.top_dir)
    
    def run_repo_command(self):
        self._error_on_sc_uninitialised()
        if self.remote:
            logger.info(f"Removing Local & Remote Branch {self.branch.name}")
        else:
            logger.info(f"Removing Local Branch {self.branch.name}")
        
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            if proj.lock_status is None:
                self._delete_branch(self.top_dir / proj.path, proj.remote)
        
        self._delete_branch(self.top_dir / '.repo' / 'manifests')
        
    def _delete_branch(self, dir: Path, remote_name: str | None = None):
        repo = Repo(dir)
        if repo.active_branch.name == self.branch.name:
            repo.git.switch(GitFlowLibrary.get_develop_branch(dir))
        repo.git.branch("-D", self.branch.name)
        if self.remote:
            if not remote_name:
                remote_name = repo.remotes[0].name
            repo.git.push(remote_name, "--delete", f"{self.branch.name}")
            try:
                repo.git.update_ref("-d", f"refs/remotes/{remote_name}/{self.branch.name}")
            except GitCommandError as e:
                logger.info("Failed to delete remote ref, may just not be fetched: %s", e)

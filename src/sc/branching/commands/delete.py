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
import subprocess
import sys

from git_flow_library import GitFlowLibrary
from sc_manifest_parser import ScManifest

from ..branch import Branch
from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class Delete(Command):
    branch: Branch
    remote: bool = False
    force: bool = False

    def run_git_command(self):
        _git_flow_delete(self.top_dir, self.branch, self.remote, self.force)
        GitFlowLibrary.delete(
            self.top_dir, self.branch.type, self.branch.suffix, self.remote)
    
    def run_repo_command(self):
        self._error_on_sc_uninitialised()
        if self.remote:
            logger.info(f"Removing Local & Remote Branch {self.branch.name}")
        else:
            logger.info(f"Removing Local Branch {self.branch.name}")
        
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            _git_flow_delete(
                self.top_dir / proj.path, self.branch, self.remote, self.force)
        
        _git_flow_delete(
            self.top_dir / '.repo' / 'manifests', self.branch, self.remote, self.force)
        
def _git_flow_delete(dir: Path, branch: Branch, remote: bool = False, force: bool = False):
    try:
        GitFlowLibrary.delete(
            dir,
            branch.type,
            branch.suffix,
            remote=remote,
            force=force
        )
    except subprocess.CalledProcessError as e:
        logger.error(e)
        sys.exit(1)

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

from pathlib import Path
import subprocess
import logging
from .command import Command
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

class Reset(Command):
    def _reset_repo(self, dir: Path | str, revision: str):
        subprocess.run(
            ["git", "reset", "--hard", revision],
            cwd = dir,
            encoding = "utf-8",
            check = False,
        )

    def run_git_command(self):
        logger.error("Not implemented for Git use Git reset instead")

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for project in manifest.projects:
            if project.lock_status is not None:
                continue

            self._reset_repo(self.top_dir/project.path,project.revision)

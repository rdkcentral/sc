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

import subprocess

from .command import Command
from sc_manifest_parser import ScManifest

class Clean(Command):
    def _clean_repo(self,dir):
        subprocess.run(
            ["git","clean","-fdx","-e",f'".repo*"'],
            cwd = dir,
            encoding = "utf-8",
            check = False,
        )

    def run_git_command(self):
        self._clean_repo(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        manifest_dir = self.top_dir / '.repo' / 'manifests'
        for project in manifest.projects:
            if project.lock_status is not None:
                continue
            self._clean_repo(self.top_dir)
        self._clean_repo(manifest_dir)

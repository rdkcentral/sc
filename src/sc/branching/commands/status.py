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
from repo_library import RepoLibrary

class Status(Command):
    def run_git_command(self):
        subprocess.run(
            ["git","status"],
            cwd = self.top_dir,
            encoding="utf-8",
            check=False,
        )

    def run_repo_command(self):
        RepoLibrary.status(self.top_dir)

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

from sc_manifest_parser import ScManifest

from .command import Command

@dataclass
class ShowBranch(Command):
    def run_git_command(self):
        pass

    def run_repo_command(self):
        return super().run_repo_command()

@dataclass
class ShowTag(Command):
    def run_git_command(self):
        pass

    def run_repo_command(self):
        return super().run_repo_command()

@dataclass
class ShowGroup(Command):
    def run_git_command(self):
        pass

    def run_repo_command(self):
        return super().run_repo_command()

@dataclass
class ShowRepoFlowConfig(Command):
    def run_git_command(self):
        pass

    def run_repo_command(self):
        return super().run_repo_command()

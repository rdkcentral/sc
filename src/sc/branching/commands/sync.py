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

import logging
import subprocess

from repo_library import RepoLibrary

from ..branch import Branch, BranchType
from .command import Command
from .pull import Pull

logger = logging.getLogger(__name__)

class Sync(Command):
    force_sync: bool
    no_checkout: bool

    def run_git_command(self):
        logger.error("No git equivalent for sc sync.")

    def run_repo_command(self):
        branch_str = RepoLibrary.get_manifest_branch(self.top_dir)
        branch = self._resolve_branch(branch_str)

        Pull(
            self.top_dir,
            branch,
            force_sync=self.force_sync,
            no_checkout=self.no_checkout
        )

    def _resolve_branch(self, branch: str):
        if branch == "master" or branch == "develop":
            return Branch(BranchType(branch))

        if "/" not in branch:
            logger.error(
                f"Invalid branch {branch} must contain '/' if not master or develop.")

        branch_type, suffix = branch.split("/", 1)

        if not BranchType.is_valid(branch_type):
            logger.error(
                f"Invalid branch {branch} must start with {', '.join(BranchType.valid_types())}.")

        return Branch(BranchType(branch_type), suffix)

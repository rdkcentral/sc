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

from git_flow_library import GitFlowLibrary

class GitFlowBranchStrategy:
    def get_target_branch(self, directory: Path, source_branch: str) -> str:
        if GitFlowLibrary.is_gitflow_enabled(directory):
            base = GitFlowLibrary.get_branch_base(source_branch, directory)
            return base if base else GitFlowLibrary.get_develop_branch(directory)
        else:
            return "develop"

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
from .git_cloner import GitCloner, GitClonerConfig

class GitFlowCloner(GitCloner):
    """Clone a git project and initialise it for git-flow."""
    def __init__(self, config: GitClonerConfig):
        super().__init__(config)

    def clone(self, directory: Path):
        """Clones the Git repository and initializes GitFlow in the cloned directory."""
        super().clone(directory)
        GitFlowLibrary.init(directory)
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
from pathlib import Path
import sys

import click
from git import GitCommandError, Repo
from pydantic import BaseModel

from .cloner import Cloner, RefType

logger = logging.getLogger(__name__)

class GitClonerConfig(BaseModel):
    uri: str
    branch: str | None = None
    no_tags: bool = False


class GitCloner(Cloner):
    """Clones a git repository.

    Args:
        uri (str): The repository URL to clone.
        directory (str, optional): The directory where the repository should be cloned.
            Defaults to None.
        branch (str, optional): The branch to clone. If None, the default branch is used.
        no_tags (bool, optional): Clone without tags.
    """

    def __init__(
            self,
            config: GitClonerConfig
        ):
        self.config = config

    def clone(self, directory: Path):
        cmd = ["git", "clone"]

        if self.config.no_tags:
            cmd.append("--no-tags")

        if self.config.branch:
            cmd.extend(["--branch", self.config.branch])

        cmd.append(self.config.uri)
        cmd.append(str(directory))

        click.secho(" ".join(cmd), fg="green")

        ref_type = self._is_branch_tag_or_sha(self.config.uri, self.config.branch)

        try:
            if ref_type == RefType.SHA:
                repo = Repo.clone_from(
                    self.config.uri,
                    directory,
                    multi_options=["--no-tags"] if self.config.no_tags else None
                )
                repo.git.fetch("origin", self.config.branch)
                repo.git.checkout(self.config.branch)
            else:
                repo = Repo.clone_from(
                    self.config.uri,
                    directory,
                    branch=self.config.branch,
                    multi_options=["--no-tags"] if self.config.no_tags else None
                )
        except GitCommandError as e:
            logger.error(f"Git error {e}")
            sys.exit(1)
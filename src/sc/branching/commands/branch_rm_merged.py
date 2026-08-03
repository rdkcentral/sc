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
from pathlib import Path

import git
from git import Repo
from git_flow_library import GitFlowLibrary

from ..branch import Branch
from .command import Command
from .delete import Delete
from sc.exceptions import ScError
from sc.prompter import Prompter
from sc.services.tickets.ticket_service import TicketService

@dataclass
class BranchRmMerged(Command):
    not_merged: bool = False
    all: bool = False
    no_prompt: bool = False
    git_only: bool = False
    dry_run: bool = False

    def run_git_command(self):
        self._verify_options()
        self._rm_merged(self.top_dir, git_only=True)

    def run_repo_command(self):
        self._error_on_sc_uninitialised()
        self._verify_options()

        if self.git_only:
            root = GitFlowLibrary.get_git_root(Path.cwd())
            if not root:
                raise ScError(f"{Path.cwd()} not a valid git repository!")
            self._rm_merged(root, self.git_only)
        else:
            self._rm_merged(self.top_dir)

    def _verify_options(self):
        if self.not_merged and self.all:
            raise ScError("Cannot pass both --all and --no-merged.")

    def _rm_merged(self, path: Path, git_only: bool = False):
        filtered_branches = self._get_feature_branches(path)

        ticket_service = TicketService()

        for branch in filtered_branches:
            ticket = ticket_service.get_ticket_from_branch(branch.name)
            print(ticket.to_terminal(one_line=True))
            print(branch.name)

            if self.dry_run:
                continue

            if self.no_prompt:
                self._delete_branch(path, branch, git_only)
            elif Prompter.yn("Delete branch?"):
                self._delete_branch(path, branch, git_only)

    def _get_feature_branches(self, path: Path) -> list[Branch]:
        try:
            repo = Repo(path)
        except git.InvalidGitRepositoryError as e:
            raise ScError(f"Invalid git repo: {path}") from e

        develop = GitFlowLibrary.get_develop_branch(path)
        master = GitFlowLibrary.get_master_branch(path)
        hotfix = GitFlowLibrary.get_config_value("prefix.hotfix", path)
        release = GitFlowLibrary.get_config_value("prefix.release", path)
        support = GitFlowLibrary.get_config_value("prefix.support", path)

        branch_filters = [develop, master, hotfix, release, support, "m/feature"]

        feature = GitFlowLibrary.get_config_value("prefix.feature", path)

        merge_type = "--merged" if not self.not_merged else "--no-merged"
        merge_type = "--all" if self.all else merge_type
        branches = repo.git.branch("-r", merge_type, develop).splitlines()

        feature_branches = [
            branch.strip().split("/", 1)[1]
            for branch in branches
            if not any(f in branch for f in branch_filters)
            and feature in branch
        ]

        return [Branch(*b.split("/", 1)) for b in feature_branches]

    def _delete_branch(self, path: Path, branch: Branch, git_only: bool):
        if git_only:
            Delete(path, branch, remote=True).run_git_command()
        else:
            Delete(path, branch, remote=True).run_repo_command()


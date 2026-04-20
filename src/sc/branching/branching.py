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

from enum import Enum
import logging
from pathlib import Path
import sys

from git import Repo
from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary

from .branch import Branch, BranchType
from .commands.checkout import Checkout
from .commands.clean import Clean
from .commands.command import Command
from .commands.finish import Finish
from .commands.group import (GroupCheckout, GroupCmd, GroupFetch, GroupPush, GroupPull,
                             GroupShow, GroupTag)
from .commands.init import Init
from .commands.list import List
from .commands.pull import Pull
from .commands.push import Push
from .commands.show import ShowBranch, ShowLog, ShowRepoFlowConfig
from .commands.start import Start
from .commands.status import Status
from .commands.tag import (TagCheck, TagCreate, TagList, TagPush,
                           TagRm, TagShow)
from .commands.reset import Reset
from .exceptions import ScInitError

logger = logging.getLogger(__name__)

class ProjectType(Enum):
    """Git or repo."""
    GIT = "git"
    REPO = "repo"

class SCBranching:
    @staticmethod
    def init(run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(Init(top_dir), project_type)

    @staticmethod
    def pull(branch_type: BranchType, name: str | None = None, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Pull(top_dir, branch),
            project_type
        )

    @staticmethod
    def start(branch_type: BranchType, name: str, base: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Start(top_dir, branch, base),
            project_type
        )

    @staticmethod
    def checkout(
        branch_type: BranchType,
        name: str | None = None,
        force: bool = False,
        verify: bool = False,
        run_dir: Path = Path.cwd(),
    ):
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Checkout(top_dir, branch, force=force, verify=verify),
            project_type
        )

    @staticmethod
    def status(
        run_dir: Path = Path.cwd(),
    ):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            Status(top_dir),
            project_type
        )

    @staticmethod
    def clean(
        run_dir: Path = Path.cwd(),
    ):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            Clean(top_dir),
            project_type
        )

    @staticmethod
    def reset(
        run_dir: Path = Path.cwd(),
    ):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            Reset(top_dir),
            project_type
        )

    @staticmethod
    def push(
        branch_type: BranchType,
        name: str | None = None,
        message: str | None = None,
        run_dir: Path = Path.cwd()
    ):
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Push(top_dir, branch, message),
            project_type
        )

    @staticmethod
    def finish(
        branch_type: BranchType,
        name: str | None = None,
        base: str | None = None,
        run_dir: Path = Path.cwd()
    ):
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Finish(top_dir, branch, base),
            project_type
        )

    @staticmethod
    def list(branch_type: BranchType, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            List(top_dir, branch_type),
            project_type
        )

    @staticmethod
    def tag_list(run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            TagList(top_dir),
            project_type
        )

    @staticmethod
    def tag_show(tag: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            TagShow(top_dir, tag),
            project_type
        )

    @staticmethod
    def tag_create(tag: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            TagCreate(top_dir, tag),
            project_type
        )

    @staticmethod
    def tag_rm(tag: str, remote: bool, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            TagRm(top_dir, tag, remote),
            project_type
        )

    @staticmethod
    def tag_push(tag: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            TagPush(top_dir, tag),
            project_type
        )

    @staticmethod
    def tag_check(tag: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            TagCheck(top_dir, tag),
            project_type
        )

    @staticmethod
    def show_branch(run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            ShowBranch(top_dir),
            project_type
        )

    @staticmethod
    def show_log(run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            ShowLog(top_dir),
            project_type
        )

    @staticmethod
    def show_repo_flow_config(run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            ShowRepoFlowConfig(top_dir),
            project_type
        )

    @staticmethod
    def group_checkout(group: str, branch: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupCheckout(top_dir, group, branch),
            project_type
        )

    @staticmethod
    def group_cmd(group: str, command: tuple[str, ...], run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupCmd(top_dir, group, command),
            project_type
        )

    @staticmethod
    def group_fetch(group: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupFetch(top_dir, group),
            project_type
        )

    @staticmethod
    def group_pull(group: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupPull(top_dir, group),
            project_type
        )

    @staticmethod
    def group_push(group: str, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupPush(top_dir, group),
            project_type
        )

    @staticmethod
    def group_show(group: str | None, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupShow(top_dir, group),
            project_type
        )

    @staticmethod
    def group_tag(
        group: str,
        tag: str,
        message: str | None,
        push: bool,
        run_dir: Path = Path.cwd()
    ):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            GroupTag(top_dir, group, tag, message, push),
            project_type
        )

def detect_project(run_dir: Path) -> tuple[Path | ProjectType]:
    if root := RepoLibrary.get_repo_root_dir(run_dir):
        return root.parent, ProjectType.REPO
    elif root := GitFlowLibrary.get_git_root(run_dir):
        return root.parent, ProjectType.GIT
    logger.error("Not in a repo project or git repository!")
    sys.exit(1)

def create_branch(
        proj_type: ProjectType,
        top_dir: Path,
        branch_type: BranchType,
        name: str | None = None
    ) -> Branch:
    if name:
        if name.startswith(f"{branch_type}/"):
            name = name.split("/", 1)[1]
        return Branch(branch_type, name)

    if branch_type in {BranchType.DEVELOP, BranchType.MASTER}:
        return Branch(branch_type)

    if proj_type == ProjectType.GIT:
        original_branch = Repo(top_dir).active_branch.name
    elif proj_type == ProjectType.REPO:
        original_branch = RepoLibrary.get_manifest_branch(top_dir)

    if original_branch.startswith(branch_type):
        return Branch(*original_branch.split('/', 1))

    logger.error(f"Branch not of type {branch_type}!")
    sys.exit(1)

def run_command_by_project_type(command: Command, project_type: ProjectType):
    if project_type == ProjectType.GIT:
        command.run_git_command()
    elif project_type == ProjectType.REPO:
        try:
            command.run_repo_command()
        except ScInitError as e:
            logger.error(e)
            sys.exit(1)
    else:
        raise RuntimeError("Should not get here.")

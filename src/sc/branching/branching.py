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

from .branch import Branch, BranchType
from .commands.checkout import Checkout
from .commands.clean import Clean
from .commands.command import Command
from .commands.finish import Finish, FinishOperationError
from .commands.init import Init
from .commands.list import List
from .commands.pull import Pull
from .commands.push import Push
from .commands.start import Start
from .commands.status import Status
from .commands.reset import Reset
from .exceptions import ScInitError
from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary

logger = logging.getLogger(__name__)

class ProjectType(Enum):
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
        logger.info(f"branch_type: {branch_type} name: {name}")
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Checkout(top_dir, branch, force=force, verify=verify),
            project_type
        )

    @staticmethod
    def sc_status(
        run_dir: Path = Path.cwd(),
    ):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            Status(top_dir),
            project_type
        )

    @staticmethod
    def sc_clean(
        run_dir: Path = Path.cwd(),
    ):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            Clean(top_dir),
            project_type
        )

    @staticmethod
    def sc_reset(
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
        run_dir: Path = Path.cwd()
    ):
        top_dir, project_type = detect_project(run_dir)
        branch = create_branch(project_type, top_dir, branch_type, name)
        run_command_by_project_type(
            Push(top_dir, branch),
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
        try:
            run_command_by_project_type(
                Finish(top_dir, branch, base),
                project_type
            )
        except FinishOperationError as e:
            logger.error(e)
            sys.exit(1)

    @staticmethod
    def list(branch_type: BranchType, run_dir: Path = Path.cwd()):
        top_dir, project_type = detect_project(run_dir)
        run_command_by_project_type(
            List(top_dir, branch_type),
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

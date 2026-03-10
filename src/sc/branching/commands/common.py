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

import git
from git import Repo
from sc_manifest_parser import ProjectElementInterface, ScManifest

from ..branch import Branch, BranchType

logger = logging.getLogger(__name__)

def get_alt_branch_name(branch: Branch, project: ProjectElementInterface) -> str | None:
    match branch.type:
        case BranchType.MASTER:
            return project.alternative_master
        case BranchType.DEVELOP:
            return project.alternative_develop
        case _:
            return None

def resolve_project_branch_name(branch: Branch, project: ProjectElementInterface) -> str:
    return get_alt_branch_name(branch, project) or branch.name

def validate_project_repos(top_dir: Path, manifest: ScManifest):
    """Exit if any project paths in a manifest are invalid."""
    error = False
    for proj in manifest.projects:
        proj_path = top_dir / proj.path
        try:
            Repo(proj_path)
        except git.NoSuchPathError:
            logger.error(
                f"[bold red]Project path {proj_path} is not a valid directory![/]",
                extra={"markup": True})
            error = True
        except git.InvalidGitRepositoryError:
            logger.error(
                f"[bold red]Project path {proj_path} is not a valid git repository![/]",
                extra={"markup": True})
            error = True
    if error:
        raise RuntimeError("Repository validation failed!")

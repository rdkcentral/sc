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
    """Raise runtime error if any project repos in a manifest are invalid."""
    errors = []
    for proj in manifest.projects:
        proj_path = top_dir / proj.path
        try:
            Repo(proj_path)
        except git.NoSuchPathError:
            errors.append(f"Project path {proj_path} is not a valid directory!")
        except git.InvalidGitRepositoryError:
            errors.append(f"Project path {proj_path} is not a valid git repository!")
    if errors:
        msg = "\n".join(errors)
        raise RuntimeError(f"Repository validation failed!\n{msg}")

def require_clean_working_tree(top_dir: Path, manifest: ScManifest):
    """Error if a project or the manifest has a dirty working tree."""
    paths = [top_dir / p.path for p in manifest.projects]
    paths.append(top_dir / '.repo' / 'manifests')

    errors = []
    for path in paths:
        proj_repo = Repo(path)

        if proj_repo.index.diff(None):
            errors.append(f"{path} working tree contains unstaged changes!")
        if proj_repo.index.diff("HEAD"):
            errors.append(f"{path} working tree contains uncommitted changes!")

    if errors:
        msg = "\n".join(errors)
        raise RuntimeError(f"Projects require clean working trees!\n{msg}")

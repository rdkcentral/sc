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

from git import Repo
from sc_manifest_parser import ScManifest

from ..models import RepoInfo
from .repo_source import RepoSource

class ManifestRepoSource(RepoSource):
    def __init__(self, top_dir: Path):
        self._top_dir = top_dir
        self.manifest_dir = top_dir / ".repo" / "manifests"

    @property
    def active_branch(self) -> str:
        return Repo(self.manifest_dir).active_branch.name

    def get_repos(self) -> list[RepoInfo]:
        """Get info of all repos in a manifest that are tracked to a branch."""
        repos = self._get_project_repos()
        repos.append(self._get_repo_info(Repo(self.manifest_dir)))

        return repos

    def _get_project_repos(self) -> list[RepoInfo]:
        """Get tracked project repos defined by the manifest."""
        manifest = ScManifest.from_repo_root(self._top_dir / ".repo")
        repos = []
        for proj in manifest.projects:
            proj_repo = Repo(self._top_dir / proj.path)
            if self._should_include_project_repo(proj_repo):
                repos.append(self._get_repo_info(proj_repo))

        return repos

    def _should_include_project_repo(self, proj_repo: Repo) -> bool:
        if proj_repo.head.is_detached:
            return False

        if not proj_repo.active_branch.tracking_branch():
            return False

        return True




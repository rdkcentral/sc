from pathlib import Path

from git import Repo
from sc_manifest_parser import ScManifest

from ..models import RepoInfo
from .repo_source import RepoSource

class ManifestRepoSource(RepoSource):
    def __init__(self, top_dir: Path):
        self.top_dir = top_dir
        self.manifest_dir = self.top_dir / ".repo" / "manifests"

    def get_active_branch(self) -> str:
        return Repo(self.manifest_dir).active_branch.name

    def get_repos(self) -> list[RepoInfo]:
        """Get info of all repos in a manifest that are tracked to a branch."""
        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")
        repos = []
        for proj in manifest.projects:
            proj_repo = Repo(self.top_dir / proj.path)
            if not proj_repo.active_branch.tracking_branch():
                continue

            repos.append(self._get_repo_info(proj_repo))

        repos.append(self._get_repo_info(Repo(self.manifest_dir)))

        return repos

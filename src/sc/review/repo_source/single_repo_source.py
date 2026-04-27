
from pathlib import Path

from git import Repo

from ..models import RepoInfo
from .repo_source import RepoSource

class SingleRepoSource(RepoSource):
    def __init__(self, top_dir: Path):
        self._top_dir = top_dir

    def get_active_branch(self) -> str:
        return Repo(self._top_dir).active_branch.name

    def get_repos(self) -> list[RepoInfo]:
        return [self._get_repo_info(Repo(self.top_dir))]

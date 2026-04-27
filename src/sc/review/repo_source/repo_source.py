from abc import ABC, abstractmethod

from git import Repo

from ..models import RepoInfo

class RepoSource(ABC):
    @property
    @abstractmethod
    def active_branch(self) -> str:
        pass

    @abstractmethod
    def get_repos(self) -> list[RepoInfo]:
        pass

    def _get_repo_info(self, repo: Repo) -> RepoInfo:
        commit = repo.head.commit

        return RepoInfo(
            branch=repo.active_branch.name,
            directory=repo.working_dir,
            remote_url=repo.remotes[0].url,
            commit_sha=commit.hexsha[:10],
            commit_author=f"{commit.author.name} <{commit.author.email}>",
            commit_date=commit.committed_datetime,
            commit_message=commit.message.strip()
        )

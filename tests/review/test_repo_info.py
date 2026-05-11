import unittest
from datetime import datetime
from pathlib import Path

from sc.review.models import RepoInfo

class TestRepoInfo(unittest.TestCase):
    def setUp(self):
        self.base_kwargs = dict(
            branch="main",
            directory=Path("."),
            commit_sha="abc123",
            commit_author="author",
            commit_date=datetime.now(),
            commit_message="msg",
        )

    def test_https_url(self):
        repo = RepoInfo(
            remote_url="https://github.com/org/repo.git",
            **self.base_kwargs
        )
        self.assertEqual(repo.repo_slug, "org/repo")

    def test_https_url_no_git_suffix(self):
        repo = RepoInfo(
            remote_url="https://github.com/org/repo",
            **self.base_kwargs
        )
        self.assertEqual(repo.repo_slug, "org/repo")

    def test_ssh_url(self):
        repo = RepoInfo(
            remote_url="git@github.com:org/repo.git",
            **self.base_kwargs
        )
        self.assertEqual(repo.repo_slug, "org/repo")

    def test_ssh_url_no_git_suffix(self):
        repo = RepoInfo(
            remote_url="git@github.com:org/repo",
            **self.base_kwargs
        )
        self.assertEqual(repo.repo_slug, "org/repo")

    def test_trailing_slash(self):
        repo = RepoInfo(
            remote_url="https://github.com/org/repo/",
            **self.base_kwargs
        )
        self.assertEqual(repo.repo_slug, "org/repo")


if __name__ == "__main__":
    unittest.main()
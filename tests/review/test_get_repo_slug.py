import unittest

from sc.review.review import get_repo_slug, match_remote_url
from sc.review.exceptions import RemoteUrlNotFound

class TestGetRepoSlug(unittest.TestCase):

    def test_https_url(self):
        url = "https://github.com/org/repo.git"
        self.assertEqual(get_repo_slug(url), "org/repo")

    def test_https_without_git_suffix(self):
        url = "https://github.com/org/repo"
        self.assertEqual(get_repo_slug(url), "org/repo")

    def test_ssh_url(self):
        url = "git@github.com:org/repo.git"
        self.assertEqual(get_repo_slug(url), "org/repo")

    def test_ssh_without_git_suffix(self):
        url = "git@github.com:org/repo"
        self.assertEqual(get_repo_slug(url), "org/repo")

    def test_nested_path(self):
        url = "https://gitlab.com/group/subgroup/repo.git"
        self.assertEqual(get_repo_slug(url), "group/subgroup/repo")

    def test_trailing_slash(self):
        url = "https://github.com/org/repo/"
        self.assertEqual(get_repo_slug(url), "org/repo")

class TestMatchRemoteUrl(unittest.TestCase):
    def test_returns_matching_pattern(self):
        url = "https://github.com/org/repo.git"
        patterns = ["github.com"]
        self.assertEqual(match_remote_url(url, patterns), "github.com")

    def test_raises_when_no_match(self):
        with self.assertRaises(RemoteUrlNotFound):
            match_remote_url("https://bitbucket.org/repo", ["github.com"])

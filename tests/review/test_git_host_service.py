import unittest
from unittest.mock import MagicMock

from sc.review.git_host_service import GitHostService, _match_remote_pattern
from sc.review.exceptions import RemoteUrlNotFound


class TestGitHostService(unittest.TestCase):

    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_factory = MagicMock()
        self.mock_strategy = MagicMock()

        self.service = GitHostService(
            git_config=self.mock_config,
            factory=self.mock_factory,
            branch_strategy=self.mock_strategy
        )

    def test_get_git_review_data(self):
        repo_info = MagicMock(
            remote_url="https://gitlab.com/org/repo",
            repo_slug="org/repo",
            branch="feature-1"
        )

        self.mock_config.get_patterns.return_value = ["gitlab.com"]
        self.mock_config.get.return_value = MagicMock(
            provider="gitlab",
            token="token",
            url="base"
        )

        mock_instance = MagicMock()
        self.mock_factory.create.return_value = mock_instance
        mock_instance.get_code_review.return_value = "review"

        result = self.service.get_git_review_data(repo_info)

        self.assertEqual(result, "review")
        mock_instance.get_code_review.assert_called_once_with("org/repo", "feature-1")

    def test_get_create_cr_url(self):
        repo_info = MagicMock(
            remote_url="https://github.com/org/repo",
            repo_slug="org/repo",
            branch="feature-1",
            directory="/repo"
        )

        self.mock_config.get_patterns.return_value = ["github.com"]
        self.mock_config.get.return_value = MagicMock(
            provider="github",
            token="token",
            url="base"
        )

        mock_instance = MagicMock()
        self.mock_factory.create.return_value = mock_instance

        self.mock_strategy.get_target_branch.return_value = "main"
        mock_instance.get_create_cr_url.return_value = "url"

        result = self.service.get_create_cr_url(repo_info)

        self.assertEqual(result, "url")
        mock_instance.get_create_cr_url.assert_called_once_with(
            "org/repo", "feature-1", "main"
        )

    def test_create_git_instance(self):
        self.mock_config.get_patterns.return_value = ["github.com"]
        git_data = MagicMock(provider="github", token="t", url="u")
        self.mock_config.get.return_value = git_data

        instance = MagicMock()
        self.mock_factory.create.return_value = instance

        result = self.service._create_git_instance("https://github.com/org/repo")

        self.assertEqual(result, instance)
        self.mock_factory.create.assert_called_once_with(
            "github", token="t", base_url="u"
        )

    def test_match_remote_pattern_success(self):
        result = _match_remote_pattern(
            "https://github.com/org/repo",
            ["gitlab.com", "github.com"]
        )
        self.assertEqual(result, "github.com")

    def test_match_remote_pattern_failure(self):
        with self.assertRaises(RemoteUrlNotFound):
            _match_remote_pattern(
                "https://bitbucket.org/org/repo",
                ["gitlab.com", "github.com"]
            )


if __name__ == "__main__":
    unittest.main()
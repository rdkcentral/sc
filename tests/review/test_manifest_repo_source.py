import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from sc.review.repo_source.manifest_repo_source import ManifestRepoSource


class TestManifestRepoSource(unittest.TestCase):
    def setUp(self):
        self.top_dir = Path("/fake/top")
        self.source = ManifestRepoSource(self.top_dir)

    @patch("sc.review.repo_source.manifest_repo_source.Repo")
    def test_active_branch(self, mock_repo):
        mock_repo.return_value.active_branch.name = "main"

        branch = self.source.active_branch

        self.assertEqual(branch, "main")
        mock_repo.assert_called_with(self.source.manifest_dir)

    @patch("sc.review.repo_source.manifest_repo_source.Repo")
    def test_should_include_project_repo_true(self, mock_repo):
        repo = MagicMock()
        repo.head.is_detached = False
        repo.active_branch.tracking_branch.return_value = "origin/main"

        result = self.source._should_include_project_repo(repo)

        self.assertTrue(result)

    def test_should_include_project_repo_detached(self):
        repo = MagicMock()
        repo.head.is_detached = True

        result = self.source._should_include_project_repo(repo)

        self.assertFalse(result)

    def test_should_include_project_repo_no_tracking(self):
        repo = MagicMock()
        repo.head.is_detached = False
        repo.active_branch.tracking_branch.return_value = None

        result = self.source._should_include_project_repo(repo)

        self.assertFalse(result)

    @patch("sc.review.repo_source.manifest_repo_source.ScManifest")
    @patch("sc.review.repo_source.manifest_repo_source.Repo")
    def test_get_project_repos_filters_correctly(self, mock_repo, mock_manifest):
        # Mock manifest projects
        proj1 = MagicMock(path="proj1")
        proj2 = MagicMock(path="proj2")
        mock_manifest.from_repo_root.return_value.projects = [proj1, proj2]

        repo1 = MagicMock()
        repo1.head.is_detached = False
        repo1.active_branch.tracking_branch.return_value = "origin/main"

        repo2 = MagicMock()
        repo2.head.is_detached = True  # excluded

        mock_repo.side_effect = [repo1, repo2]

        self.source._get_repo_info = MagicMock(side_effect=["info1"])

        repos = self.source._get_project_repos()

        self.assertEqual(repos, ["info1"])
        self.source._get_repo_info.assert_called_once_with(repo1)

    @patch("sc.review.repo_source.manifest_repo_source.Repo")
    def test_get_repos_includes_manifest_repo(self, mock_repo):
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance

        self.source._get_project_repos = MagicMock(return_value=["proj_info"])
        self.source._get_repo_info = MagicMock(return_value="manifest_info")

        repos = self.source.get_repos()

        self.assertEqual(repos, ["proj_info", "manifest_info"])
        self.source._get_repo_info.assert_called_with(mock_repo_instance)

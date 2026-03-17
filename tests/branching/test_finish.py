
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from repo_client_creator import RepoTestClientCreator

class TestFinish(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branch("master")
        self.repo_client.add_branch("develop")

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_finish(self):
        self.repo_client.add_branch("feature/donut")
        path = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "feature", "finish"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        self.assertEqual(
            Repo(path / ".repo" / "manifests").active_branch.name, "develop")
        proj_path = path / manifest.projects[0].path
        self.assertEqual(Repo(proj_path).active_branch.name, "develop")
        self.assertEqual(
            Repo(proj_path).active_branch.commit.hexsha, manifest.projects[0].revision)
        self.assertEqual((proj_path / "README.md").read_text(), "feature/donut")

    def test_release_finish(self):
        self.repo_client.add_branch("release/donut")
        path = self.repo_client.create("release/donut")

        # Input sets the tag message
        subprocess.run(["sc", "release", "finish"], input="donut\n", text=True, cwd=path)

        manifest_repo = Repo(path / ".repo" / "manifests")
        self.assertIn("donut", manifest_repo.tags)
        self.assertEqual(manifest_repo.active_branch.name, "develop")

    def test_hotfix_finish(self):
        self.repo_client.add_branch("support/donut")
        self.repo_client.add_branch("hotfix/donut")
        path = self.repo_client.create("hotfix/donut")
        manifest_repo = Repo(path / ".repo" / "manifests")
        subprocess.run(["sc", "support", "pull", "donut"], cwd=path)

        # Input sets the tag message
        subprocess.run(
            ["sc", "hotfix", "finish", "donut", "support/donut"],
            input="donut\n",
            text=True,
            cwd=path
        )

        manifest_repo = Repo(path / ".repo" / "manifests")
        self.assertIn("donut", manifest_repo.tags)
        self.assertEqual(manifest_repo.active_branch.name, "support/donut")

    def test_not_finish_read_only(self):
        self.repo_client.add_branch("feature/donut")
        self.repo_client.add_annotation("GIT_LOCK_STATUS", "READ_ONLY")
        path = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "feature", "finish"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertTrue(proj_repo.head.is_detached)
        self.assertNotIn("donut", proj_repo.tags)

    def test_tag_tag_only(self):
        self.repo_client.add_branch("release/donut")
        self.repo_client.add_annotation("GIT_LOCK_STATUS", "TAG_ONLY")
        path = self.repo_client.create("release/donut")

        subprocess.run(["sc", "release", "finish"], input="donut\n", text=True, cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertTrue(proj_repo.head.is_detached)
        self.assertIn("donut", proj_repo.tags)

if __name__ == "__main__":
    unittest.main()



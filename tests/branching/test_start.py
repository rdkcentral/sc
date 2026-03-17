import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from repo_client_creator import RepoTestClientCreator

class TestStart(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branch("master")
        self.repo_client.add_branch("develop")

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_start(self):
        path = self.repo_client.create("develop")

        subprocess.run(["sc", "feature", "start", "donut"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertEqual(proj_repo.active_branch.name, "feature/donut")
        self.assertTrue(
            any(ref.name == "feature/donut"
                for ref in self.repo_client.man_remote.branches))

    def test_release_start(self):
        path = self.repo_client.create("develop")

        subprocess.run(["sc", "release", "start", "donut"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertEqual(proj_repo.active_branch.name, "release/donut")
        self.assertTrue(
            any(ref.name == "release/donut"
                for ref in self.repo_client.man_remote.branches))

    def test_feature_start_base(self):
        path = self.repo_client.create("develop")

        subprocess.run(["sc", "feature", "start", "donut", "master"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertNotEqual(proj_repo.branches["develop"].commit.hexsha,
                            proj_repo.active_branch.commit.hexsha)
        self.assertEqual(proj_repo.branches["master"].commit.hexsha,
                         proj_repo.active_branch.commit.hexsha)

if __name__ == "__main__":
    unittest.main()


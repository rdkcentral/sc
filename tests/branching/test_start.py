import subprocess
import unittest

from git import Repo

from .repo_client_creator import RepoTestClientCreator

class TestStart(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_start(self):
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "feature", "start", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "feature/donut")
        self.assertTrue(
            any(ref.name == "feature/donut"
                for ref in self.repo_client.man_remote.branches))

    def test_release_start(self):
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "release", "start", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "release/donut")
        self.assertTrue(
            any(ref.name == "release/donut"
                for ref in self.repo_client.man_remote.branches))

    def test_hotfix_start_base(self):
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "hotfix", "start", "donut", "master"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertNotEqual(proj_repo.branches["develop"].commit.hexsha,
                            proj_repo.active_branch.commit.hexsha)
        self.assertEqual(proj_repo.branches["master"].commit.hexsha,
                         proj_repo.active_branch.commit.hexsha)

    def fails_starting_branch_that_already_exists(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "feature", "start", "donut"],
                cwd=top_dir, capture_output=True, check=True)

        self.assertIn("cannot be started", cm.exception.stdout)

if __name__ == "__main__":
    unittest.main()


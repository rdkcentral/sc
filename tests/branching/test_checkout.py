from pathlib import Path
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from repo_client_creator import RepoTestClientCreator

class TestCheckout(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branch("master")
        self.repo_client.add_branch("develop")
        self.repo_client.add_branch("feature/donut")

    def tearDown(self):
        self.repo_client.cleanup()

    def test_checkout(self):
        path = self.repo_client.create("develop")

        subprocess.run(["sc", "feature", "checkout", "donut"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertEqual(
            manifest.projects[0].revision, proj_repo.active_branch.commit.hexsha)
        self.assertEqual(proj_repo.active_branch.name, "feature/donut")
        manifest_repo = Repo(path / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "feature/donut")

    def test_develop_checkout(self):
        path = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "develop", "checkout"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertEqual(
            manifest.projects[0].revision, proj_repo.active_branch.commit.hexsha)
        self.assertEqual(proj_repo.active_branch.name, "develop")

    def test_develop_checkout_force(self):
        path = self.repo_client.create("feature/donut")
        manifest = ScManifest.from_repo_root(path / ".repo")
        test_file = path / manifest.projects[0].path / "README.md"
        test_file.write_text("donut")

        subprocess.run(["sc", "develop", "checkout", "-f"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertEqual(test_file.read_text(), "develop")

    def test_checkout_error_with_change_and_no_force(self):
        path = self.repo_client.create("feature/donut")
        manifest = ScManifest.from_repo_root(path / ".repo")
        test_file = path / manifest.projects[0].path / "README.md"
        test_file.unlink()

        output = subprocess.run(["sc", "develop", "checkout"], cwd=path, capture_output=True)

        self.assertNotEqual(output.returncode, 0)


if __name__ == "__main__":
    unittest.main()

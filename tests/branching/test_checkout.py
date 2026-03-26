import shutil
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from .repo_client_creator import RepoTestClientCreator

class TestCheckout(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_checkout(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "feature", "checkout", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)
        self.assertEqual(proj_repo.active_branch.name, "feature/donut")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "feature/donut")

    def test_develop_checkout(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "develop", "checkout"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "develop")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)

    def test_develop_checkout_force(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        test_file = top_dir / proj.name / "README.md"
        test_file.write_text("donut")

        subprocess.run(["sc", "develop", "checkout", "-f"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertEqual(test_file.read_text(), "develop")
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)

    def test_checkout_error_with_change_and_no_force(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        test_file = top_dir / proj.name / "README.md"
        test_file.unlink()

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "develop", "checkout"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertNotEqual(cm.exception.returncode, 0)
        self.assertIn("clean working tree", cm.exception.stderr)

    def test_alt_develop_checkout(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project(alt_develop="alt_develop")
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "develop", "checkout"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "alt_develop")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)

    def test_alt_master_checkout(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project(alt_master="alt_master")
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "master", "checkout"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "alt_master")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "master")

    def test_hotfix_checkout(self):
        self.repo_client.add_branches(["master", "develop", "hotfix/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "hotfix", "checkout", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "hotfix/donut")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "hotfix/donut")
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)

    def test_release_checkout(self):
        self.repo_client.add_branches(["master", "develop", "release/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "release", "checkout", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "release/donut")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "release/donut")
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)

    def test_support_checkout(self):
        self.repo_client.add_branches(["master", "develop", "support/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "support", "checkout", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "support/donut")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(manifest_repo.active_branch.name, "support/donut")
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            manifest.get_project_by_name(proj.name).revision,
            proj_repo.active_branch.commit.hexsha)

    def test_checkout_fails_on_missing_project(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        shutil.rmtree(top_dir / proj.name)

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "develop", "checkout"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("Repository validation failed", cm.exception.stderr)

if __name__ == "__main__":
    unittest.main()

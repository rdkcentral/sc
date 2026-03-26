from pathlib import Path
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

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

    def test_fails_starting_branch_that_already_exists(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "feature", "start", "donut"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("cannot be started", cm.exception.stdout)

    def test_hotfix_start_base(self):
        self.repo_client.add_branches(["master", "develop", "support/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "hotfix", "start", "donut", "support/donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertNotEqual(proj_repo.branches["develop"].commit.hexsha,
                            proj_repo.active_branch.commit.hexsha)
        self.assertEqual(proj_repo.branches["support/donut"].commit.hexsha,
                         proj_repo.active_branch.commit.hexsha)

    def test_hotfix_fail_to_start_from_non_support_base(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "hotfix", "start", "donut", "feature/donut"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn(
            "You can only start hotfix branches from support branches",
            cm.exception.stdout)

    def test_support_start_from_tag(self):
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("master")
        tagged_sha = proj.repo.active_branch.commit.hexsha
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("master")
        self.repo_client.man_repo.git.tag("test-tag")
        self.repo_client.man_repo.git.push("--tags")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End remote mutation ---

        subprocess.run(["sc", "support", "start", "donut", "test-tag"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.name, "support/donut")
        self.assertEqual(proj_repo.head.commit.hexsha, tagged_sha)

if __name__ == "__main__":
    unittest.main()


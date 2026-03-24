from pathlib import Path
import subprocess
import unittest

from git import Repo
from .repo_client_creator import RepoTestClientCreator
from sc_manifest_parser import ScManifest

class TestPull(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_pull(self):
        """Simulate another develop using feature push
        by updating repo and manifest revision. Then pull.
        """
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("feature/donut")
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("feature/donut")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "feature", "pull", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)
        self.assertEqual(proj_repo.active_branch.name, "feature/donut")

    def test_conflicting_pull(self):
        """Simulate an extra commit remote and locally and test for merge conflict.
        """
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        # --- Mutate remote state ---
        proj.repo.git.checkout("feature/donut")
        (Path(proj.repo.working_dir) / "test_file").write_text("remote file")
        proj.repo.git.add(A=True)
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("feature/donut")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---
        local_proj_path = top_dir / proj.name
        (local_proj_path / "test_file").write_text("local file")
        local_repo = Repo(local_proj_path)
        local_repo.git.add(A=True)
        local_repo.git.commit(m="conflicting commit")

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "feature", "pull"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("Please resolve merge conflicts", cm.exception.stdout)

    def test_fail_trying_to_pull_non_existing(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        output = subprocess.run(["sc", "feature", "pull", "fake"], cwd=top_dir)

        self.assertNotEqual(output.returncode, 0)

    def test_develop_pull(self):
        """Simulate another develop using feature push
        by updating repo and manifest revision. Then pull.
        """
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("develop")
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("develop")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "develop", "pull"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)
        self.assertEqual(proj_repo.active_branch.name, "develop")

    def test_master_pull(self):
        """Simulate another develop using feature push
        by updating repo and manifest revision. Then pull.
        """
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("master")
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("master")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "master", "pull"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)
        self.assertEqual(proj_repo.active_branch.name, "master")

    def test_release_pull(self):
        self.repo_client.add_branches(["master", "develop", "release/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("release/donut")
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("release/donut")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "release", "pull", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)
        self.assertEqual(proj_repo.active_branch.name, "release/donut")

    def test_support_pull(self):
        self.repo_client.add_branches(["master", "develop", "support/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("support/donut")
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("support/donut")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "support", "pull", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)
        self.assertEqual(proj_repo.active_branch.name, "support/donut")

    def test_hotfix_pull(self):
        self.repo_client.add_branches(["master", "develop", "hotfix/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")
        # --- Mutate remote state ---
        proj.repo.git.checkout("hotfix/donut")
        proj.repo.git.commit("--allow-empty", m="extra_commit")
        proj.repo.git.push()
        new_sha = proj.repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("hotfix/donut")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "hotfix", "pull", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)
        self.assertEqual(proj_repo.active_branch.name, "hotfix/donut")

if __name__ == "__main__":
    unittest.main()
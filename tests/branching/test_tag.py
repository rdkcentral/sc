from pathlib import Path
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from .repo_client_creator import RepoTestClientCreator

class TestTagCheckout(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_tag_checkout(self):
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
        manifest_tagged_sha = self.repo_client.man_repo.head.commit.hexsha
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End remote mutation ---

        subprocess.run(["sc", "tag", "checkout", "test-tag"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        self.assertEqual(proj_repo.head.commit.hexsha, tagged_sha)
        man_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(man_repo.head.commit.hexsha, manifest_tagged_sha)

    def test_tag_checkout_fails_if_tag_doesnt_exist(self):
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "tag", "checkout", "fake-tag"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("not found in manifest repo", cm.exception.stdout)


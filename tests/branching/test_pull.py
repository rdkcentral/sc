from pathlib import Path
import subprocess
import unittest

from git import Repo
from repo_client_creator import RepoTestClientCreator
from sc_manifest_parser import ScManifest

class TestPull(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branch("master")
        self.repo_client.add_branch("develop")
        self.repo_client.add_branch("feature/donut")

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_pull(self):
        """Simulate another develop using feature push
        by updating repo and manifest revision. Then pull.
        """
        path = self.repo_client.create("develop")
        # --- Mutate remote state ---
        self.repo_client.project_repo.git.checkout("feature/donut")
        self.repo_client.project_repo.git.commit("--allow-empty", m="extra_commit")
        self.repo_client.project_repo.git.push()
        new_sha = self.repo_client.project_repo.active_branch.commit.hexsha

        self.repo_client.man_repo.git.checkout("feature/donut")
        man = ScManifest(Path(self.repo_client.man_repo.working_dir) / "manifest.xml")
        man.projects[0].revision = new_sha
        man.write()
        self.repo_client.man_repo.git.add(A=True)
        self.repo_client.man_repo.git.commit(m="extra commit")
        self.repo_client.man_repo.git.push()
        # --- End mutation ---

        subprocess.run(["sc", "feature", "pull", "donut"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_repo = Repo(path / manifest.projects[0].path)
        self.assertEqual(proj_repo.active_branch.commit.hexsha, new_sha)

    def test_fail_trying_to_pull_non_existing(self):
        path = self.repo_client.create("develop")

        output = subprocess.run(["sc", "feature", "pull", "fake"], cwd=path)

        self.assertNotEqual(output.returncode, 0)

if __name__ == "__main__":
    unittest.main()
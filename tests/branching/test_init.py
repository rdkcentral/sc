import subprocess
import unittest

from git import Repo
from git_flow_library import GitFlowLibrary
from sc_manifest_parser import ScManifest

from repo_client_creator import RepoTestClientCreator

class TestInit(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branch("master")
        self.repo_client.add_branch("develop")

    def tearDown(self):
        self.repo_client.cleanup()

    def test_init(self):
        path = self.repo_client.create("develop", sc_init=False)

        subprocess.run(["sc", "init"], cwd=path)

        self.assertTrue(GitFlowLibrary.is_gitflow_enabled(path / '.repo' / 'manifests'))
        manifest = ScManifest.from_repo_root(path / ".repo")
        self.assertTrue(
            GitFlowLibrary.is_gitflow_enabled(path / manifest.projects[0].path))

    def test_init_with_alt_branches(self):
        self.repo_client.set_alt_develop("donut-develop")
        self.repo_client.set_alt_master("donut-master")
        path = self.repo_client.create("develop", sc_init=False)

        subprocess.run(["sc", "init"], cwd=path)

        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_path = path / manifest.projects[0].path
        self.assertEqual(GitFlowLibrary.get_develop_branch(proj_path), "donut-develop")
        self.assertEqual(GitFlowLibrary.get_master_branch(proj_path), "donut-master")

if __name__ == "__main__":
    unittest.main()
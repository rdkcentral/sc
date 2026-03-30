import subprocess
import unittest

from git_flow_library import GitFlowLibrary
from sc_manifest_parser import ScManifest

from .repo_client_creator import RepoTestClientCreator

class TestInit(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branches(["master", "develop"])

    def tearDown(self):
        self.repo_client.cleanup()

    def test_init(self):
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop", sc_init=False)

        subprocess.run(["sc", "init"], cwd=top_dir)

        self.assertTrue(GitFlowLibrary.is_gitflow_enabled(top_dir / '.repo' / 'manifests'))
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertTrue(GitFlowLibrary.is_gitflow_enabled(top_dir / proj.name))

    def test_init_with_alt_branches(self):
        proj = self.repo_client.add_project(
            alt_develop="donut-develop", alt_master="donut-master")
        top_dir = self.repo_client.create("develop", sc_init=False)

        subprocess.run(["sc", "init"], cwd=top_dir)

        self.assertEqual(
            GitFlowLibrary.get_develop_branch(top_dir / proj.name), "donut-develop")
        self.assertEqual(
            GitFlowLibrary.get_master_branch(top_dir / proj.name), "donut-master")

if __name__ == "__main__":
    unittest.main()
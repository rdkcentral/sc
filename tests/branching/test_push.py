from pathlib import Path
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from repo_client_creator import RepoTestClientCreator

class TestPush(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()
        self.repo_client.add_branch("master")
        self.repo_client.add_branch("develop")

    def tearDown(self):
        self.repo_client.cleanup()

    def test_push(self):
        self.repo_client.add_branch("feature/donut")
        path = self.repo_client.create("feature/donut")
        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_dir = path / manifest.projects[0].path
        (proj_dir / 'donut').touch()
        proj_repo = Repo(proj_dir)
        proj_repo.git.add(A=True)
        proj_repo.git.commit(m="donut")
        new_sha = proj_repo.head.commit.hexsha

        subprocess.run(
            ["sc", "feature", "push"],
            cwd=path,
            input="donut\n",
            text=True
        )

        manifest = ScManifest.from_repo_root(path / ".repo")
        self.assertEqual(manifest.projects[0].revision, new_sha)
        self.assertEqual(
            self.repo_client.project_remote.refs["feature/donut"].commit.hexsha,
            new_sha)

    def test_push_tag_only_pushes_tag(self):
        self.repo_client.add_annotation("GIT_LOCK_STATUS", "TAG_ONLY")
        path = self.repo_client.create("develop")
        manifest = ScManifest.from_repo_root(path / ".repo")
        proj_dir = path / manifest.projects[0].path
        (proj_dir / 'donut').touch()
        proj_repo = Repo(proj_dir)
        proj_repo.git.add(A=True)
        proj_repo.git.commit(m="donut")
        proj_repo.git.tag("donut")
        new_sha = proj_repo.head.commit.hexsha

        subprocess.run(
            ["sc", "develop", "push"],
            cwd=path,
            input="donut\n",
            text=True
        )

        manifest = ScManifest.from_repo_root(path / ".repo")
        self.assertEqual(manifest.projects[0].revision, new_sha)
        self.assertNotEqual(
            self.repo_client.project_remote.refs["develop"].commit.hexsha, new_sha)
        self.assertIn(
            "donut", self.repo_client.project_remote.tags)

if __name__ == "__main__":
    unittest.main()
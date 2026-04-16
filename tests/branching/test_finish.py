# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shutil
import subprocess
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from .repo_client_creator import RepoTestClientCreator

class TestFinish(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_finish(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"}
        )
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"}
        )
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "feature", "finish"], cwd=top_dir)

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        self.assertEqual(
            Repo(top_dir / ".repo" / "manifests").active_branch.name, "develop")
        self.assertEqual(Repo(top_dir / proj.name).active_branch.name, "develop")
        self.assertEqual(
            Repo(top_dir / proj.name).active_branch.commit.hexsha,
            manifest.get_project_by_name(proj.name).revision
        )
        self.assertEqual((top_dir / proj.name / "README.md").read_text(), "feature/donut")
        # READ_ONLY doesn't tag and doesn't finish
        read_only_proj_repo = Repo(top_dir / read_only_proj.name)
        self.assertTrue(read_only_proj_repo.head.is_detached)
        self.assertNotIn("donut", read_only_proj_repo.tags)
        self.assertEqual(
            read_only_proj.repo.heads["feature/donut"].commit.hexsha,
            read_only_proj_repo.head.commit.hexsha)
        # TAG_ONLY doesn't tag and doesn't finish
        tag_only_proj_repo = Repo(top_dir / tag_only_proj.name)
        self.assertTrue(tag_only_proj_repo.head.is_detached)
        self.assertNotIn("donut", tag_only_proj_repo.tags)
        self.assertEqual(
            tag_only_proj.repo.heads["feature/donut"].commit.hexsha,
            tag_only_proj_repo.head.commit.hexsha)

    def test_release_finish(self):
        self.repo_client.add_branches(["master", "develop", "release/donut"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"}
        )
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"}
        )
        top_dir = self.repo_client.create("release/donut")

        subprocess.run(
            ["sc", "release", "finish"], input="tag message\n", text=True, cwd=top_dir)

        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertIn("donut", manifest_repo.tags)
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        # Unlocked project finishes and tags
        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        unlocked_proj_repo = Repo(top_dir / unlocked_proj.name)
        self.assertEqual(
            unlocked_proj_repo.active_branch.commit.hexsha,
            manifest.get_project_by_name(unlocked_proj.name).revision
        )
        self.assertEqual(
            (top_dir / unlocked_proj.name / "README.md").read_text(), "release/donut")
        self.assertIn("donut", unlocked_proj_repo.tags)
        # READ_ONLY doesn't tag and doesn't finish
        read_only_proj_repo = Repo(top_dir / read_only_proj.name)
        self.assertTrue(read_only_proj_repo.head.is_detached)
        self.assertNotIn("donut", read_only_proj_repo.tags)
        self.assertEqual(
            read_only_proj.repo.heads["release/donut"].commit.hexsha,
            read_only_proj_repo.head.commit.hexsha)
        # TAG_ONLY tags but doesn't finish
        tag_only_proj_repo = Repo(top_dir / tag_only_proj.name)
        self.assertTrue(tag_only_proj_repo.head.is_detached)
        self.assertIn("donut", tag_only_proj_repo.tags)
        self.assertEqual(
            tag_only_proj.repo.heads["release/donut"].commit.hexsha,
            tag_only_proj_repo.head.commit.hexsha)

    def test_hotfix_finish(self):
        self.repo_client.add_branches(
            ["master", "develop", "support/donut", "hotfix/donut"])
        proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"}
        )
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"}
        )
        top_dir = self.repo_client.create("hotfix/donut")
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        subprocess.run(["sc", "support", "pull", "donut"], cwd=top_dir)

        # Input sets the tag message
        subprocess.run(
            ["sc", "hotfix", "finish", "donut", "support/donut"],
            input="donut\n",
            text=True,
            cwd=top_dir
        )

        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertIn("donut", manifest_repo.tags)
        self.assertEqual(manifest_repo.active_branch.name, "support/donut")
        self.assertEqual((top_dir / proj.name / "README.md").read_text(), "hotfix/donut")
        # READ_ONLY doesn't tag and doesn't finish
        read_only_proj_repo = Repo(top_dir / read_only_proj.name)
        self.assertTrue(read_only_proj_repo.head.is_detached)
        self.assertNotIn("donut", read_only_proj_repo.tags)
        self.assertEqual(
            read_only_proj.repo.heads["hotfix/donut"].commit.hexsha,
            read_only_proj_repo.head.commit.hexsha)
        # TAG_ONLY tags but doesn't finish
        tag_only_proj_repo = Repo(top_dir / tag_only_proj.name)
        self.assertTrue(tag_only_proj_repo.head.is_detached)
        self.assertIn("donut", tag_only_proj_repo.tags)
        self.assertEqual(
            tag_only_proj.repo.heads["hotfix/donut"].commit.hexsha,
            tag_only_proj_repo.head.commit.hexsha)

    def test_finish_fails_on_missing_project(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        shutil.rmtree(top_dir / proj.name)

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "feature", "finish"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("Repository validation failed", cm.exception.stdout)

    def test_finish_fails_on_unclean_tree(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        (top_dir / proj.name / "README.md").unlink()

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "feature", "finish"],
                cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("require clean working tree", cm.exception.stdout)

if __name__ == "__main__":
    unittest.main()

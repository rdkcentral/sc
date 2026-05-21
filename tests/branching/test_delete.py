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

import subprocess
import unittest

from git import Repo

from .repo_client_creator import RepoTestClientCreator

class TestDelete(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_delete(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "feature", "delete", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertFalse("feature/donut" in [b.name for b in proj_repo.branches])
        self.assertTrue(_remote_branch_exists(proj_repo, "feature/donut"))
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        self.assertFalse("feature/donut" in [b.name for b in manifest_repo.branches])
        self.assertTrue(_remote_branch_exists(manifest_repo, "feature/donut"))

    def test_release_delete(self):
        self.repo_client.add_branches(["master", "develop", "release/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("release/donut")

        subprocess.run(["sc", "release", "delete", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertFalse("release/donut" in [b.name for b in proj_repo.branches])
        self.assertTrue(_remote_branch_exists(proj_repo, "release/donut"))
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        self.assertFalse("release/donut" in [b.name for b in manifest_repo.branches])
        self.assertTrue(_remote_branch_exists(manifest_repo, "release/donut"))
    
    def test_hotfix_delete(self):
        self.repo_client.add_branches(["master", "develop", "hotfix/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("hotfix/donut")

        subprocess.run(["sc", "hotfix", "delete", "donut"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertFalse("hotfix/donut" in [b.name for b in proj_repo.branches])
        self.assertTrue(_remote_branch_exists(proj_repo, "hotfix/donut"))
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        self.assertFalse("hotfix/donut" in [b.name for b in manifest_repo.branches])
        self.assertTrue(_remote_branch_exists(manifest_repo, "hotfix/donut"))

    def test_feature_delete_remote(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "feature", "delete", "donut", "-r"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertFalse("feature/donut" in [b.name for b in proj_repo.branches])
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/donut"))
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        self.assertFalse("feature/donut" in [b.name for b in manifest_repo.branches])
        self.assertFalse(_remote_branch_exists(manifest_repo, "feature/donut"))

def _remote_branch_exists(repo: Repo, branch: str) -> bool:
    out = repo.git.ls_remote("--heads", repo.remotes[0].name, branch)
    return bool(out.strip())

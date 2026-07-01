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

def _remote_branch_exists(repo: Repo, branch: str) -> bool:
    out = repo.git.ls_remote("--heads", repo.remotes[0].name, branch)
    return bool(out.strip())

class TestBranchRename(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_branch_rename(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(["sc", "branch", "rename", "feature/donut", "feature/pizza"], cwd=top_dir)

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "feature/pizza")
        self.assertEqual(manifest_repo.active_branch.name, "feature/pizza")
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/donut"))
        self.assertTrue(_remote_branch_exists(proj_repo, "feature/pizza"))

    def test_branch_rename_can_be_rerun(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(
            ["sc", "branch", "rename", "feature/donut", "feature/pizza"],
            cwd=top_dir,
            check=True,
        )
        subprocess.run(
            ["sc", "branch", "rename", "feature/donut", "feature/pizza"],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "feature/pizza")
        self.assertEqual(manifest_repo.active_branch.name, "feature/pizza")
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/donut"))
        self.assertTrue(_remote_branch_exists(proj_repo, "feature/pizza"))

    def test_branch_rename_skips_when_neither_branch_exists(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(
            ["sc", "branch", "rename", "feature/missing", "feature/pizza"],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertEqual(manifest_repo.active_branch.name, "develop")
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/missing"))
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/pizza"))

    def test_branch_rename_skips_when_both_branches_exist(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut", "feature/pizza"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(
            ["sc", "branch", "rename", "feature/donut", "feature/pizza"],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "feature/donut")
        self.assertEqual(manifest_repo.active_branch.name, "feature/donut")
        self.assertTrue(_remote_branch_exists(proj_repo, "feature/donut"))
        self.assertTrue(_remote_branch_exists(proj_repo, "feature/pizza"))

    def test_branch_rename_when_remote_old_branch_does_not_exist(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        proj_repo = Repo(top_dir / proj.name)
        proj_repo.git.push(proj_repo.remotes[0].name, "--delete", "feature/donut")

        subprocess.run(
            ["sc", "branch", "rename", "feature/donut", "feature/pizza"],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")
        self.assertEqual(proj_repo.active_branch.name, "feature/pizza")
        self.assertEqual(manifest_repo.active_branch.name, "feature/pizza")
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/donut"))
        self.assertFalse(_remote_branch_exists(proj_repo, "feature/pizza"))

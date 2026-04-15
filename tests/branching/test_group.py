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
from sc_manifest_parser import ScManifest

from .repo_client_creator import RepoTestClientCreator

class TestGroup(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_sc_group_show_with_group_passed(self):
        self.repo_client.add_branches(["master", "develop"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")

        output = subprocess.run(
            ["sc", "group", "show", "GROUPA"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn(proj_a.name, output.stdout)
        self.assertNotIn(proj_b.name, output.stdout)

    def test_sc_group_show_with_no_group_passed(self):
        self.repo_client.add_branches(["master", "develop"])
        self.repo_client.add_project(groups="GROUPA")
        self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")

        output = subprocess.run(
            ["sc", "group", "show"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("GROUPA", output.stdout)
        self.assertIn("GROUPB", output.stdout)

    def test_sc_group_tag(self):
        self.repo_client.add_branches(["master", "develop"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")

        subprocess.run(
            ["sc", "group", "tag", "GROUPA", "group_tag", "-m", "TAG_MSG", "--push"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn("group_tag", [t.name for t in Repo(top_dir / proj_a.name).tags])
        self.assertIn(
            "TAG_MSG", Repo(top_dir / proj_a.name).tags["group_tag"].tag.message)
        self.assertIn("group_tag", [t.name for t in proj_a.remote.tags])
        self.assertNotIn("group_tag", [t.name for t in Repo(top_dir / proj_b.name).tags])
        self.assertNotIn("group_tag", [t.name for t in proj_b.remote.tags])

    def test_sc_group_checkout(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")

        subprocess.run(
            ["sc", "group", "checkout", "GROUPA", "feature/donut"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertEqual(Repo(top_dir / proj_a.name).active_branch.name, "feature/donut")
        self.assertEqual(Repo(top_dir / proj_b.name).active_branch.name, "develop")

    def test_sc_group_cmd(self):
        self.repo_client.add_branches(["master", "develop"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")

        output = subprocess.run(
            ["sc", "group", "cmd", "GROUPA", "pwd"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertIn(str(top_dir / proj_a.name), output.stdout)
        self.assertNotIn(str(top_dir / proj_b.name), output.stdout)

    def test_sc_group_pull(self):
        self.repo_client.add_branches(["master", "develop"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")
        proj_a.repo.git.commit("--allow-empty", m="New commit")
        proj_a.repo.git.push()
        proj_a_new_sha = proj_a.repo.active_branch.commit.hexsha
        proj_b.repo.git.commit("--allow-empty", m="New commit")
        proj_b.repo.git.push
        proj_b_new_sha = proj_b.repo.active_branch.commit.hexsha

        subprocess.run(
            ["sc", "group", "pull", "GROUPA"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertEqual(
            Repo(top_dir / proj_a.name).active_branch.commit.hexsha, proj_a_new_sha)
        self.assertNotEqual(
            Repo(top_dir / proj_b.name).active_branch.commit.hexsha, proj_b_new_sha)

    def test_sc_group_fetch(self):
        self.repo_client.add_branches(["master", "develop"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")
        proj_a.repo.git.commit("--allow-empty", m="New commit")
        proj_a.repo.git.push()
        proj_a_new_sha = proj_a.repo.active_branch.commit.hexsha
        proj_b.repo.git.commit("--allow-empty", m="New commit")
        proj_b.repo.git.push
        proj_b_new_sha = proj_b.repo.active_branch.commit.hexsha

        subprocess.run(
            ["sc", "group", "fetch", "GROUPA"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertEqual(
            Repo(top_dir / proj_a.name).refs["sc-testing/develop"].commit.hexsha,
            proj_a_new_sha)
        self.assertNotEqual(
            Repo(top_dir / proj_b.name).refs["sc-testing/develop"].commit.hexsha,
            proj_b_new_sha)

    def test_sc_group_push(self):
        self.repo_client.add_branches(["master", "develop"])
        proj_a = self.repo_client.add_project(groups="GROUPA")
        proj_b = self.repo_client.add_project(groups="GROUPB")
        top_dir = self.repo_client.create("develop")
        Repo(top_dir / proj_a.name).git.commit("--allow-empty", m="New commit")
        proj_a_new_sha = Repo(top_dir / proj_a.name).active_branch.commit.hexsha
        Repo(top_dir / proj_b.name).git.commit("--allow-empty", m="New commit")
        proj_b_new_sha = Repo(top_dir / proj_b.name).active_branch.commit.hexsha

        subprocess.run(
            ["sc", "group", "push", "GROUPA"],
            cwd=top_dir, capture_output=True, check=True, text=True)

        self.assertEqual(proj_a.remote.branches["develop"].commit.hexsha, proj_a_new_sha)
        self.assertNotEqual(proj_b.remote.branches["develop"].commit.hexsha,
                            proj_b_new_sha)


if __name__ == "__main__":
    unittest.main()
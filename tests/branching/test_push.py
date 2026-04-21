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
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

from git import Repo
from sc_manifest_parser import ScManifest

from .repo_client_creator import RepoTestClientCreator

class TestPush(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override git's commit editor
        cls.script = tempfile.NamedTemporaryFile(delete=False, mode="w")
        cls.script.write("#!/usr/bin/env sh\necho test > \"$1\"\n")
        cls.script.close()

        os.chmod(cls.script.name, os.stat(cls.script.name).st_mode | stat.S_IEXEC)

        cls.env = os.environ.copy()
        cls.env["GIT_EDITOR"] = cls.script.name

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.script.name)

    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_feature_push(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"})
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"})
        top_dir = self.repo_client.create("feature/donut")
        for proj in [unlocked_proj, tag_only_proj, read_only_proj]:
            proj_dir = top_dir / proj.name
            (proj_dir / 'donut').touch()
            proj_repo = Repo(proj_dir)
            proj_repo.git.add(A=True)
            proj_repo.git.commit(m="donut")
            proj_repo.git.tag("test-tag")
        unlocked_sha = Repo(top_dir / unlocked_proj.name).head.commit.hexsha
        tag_only_sha = Repo(top_dir / tag_only_proj.name).head.commit.hexsha
        read_only_sha = Repo(top_dir / read_only_proj.name).head.commit.hexsha

        subprocess.run(
            ["sc", "feature", "push"],
            cwd=top_dir, text=True, env=self.env
        )

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        # Unlocked pushes and updates manifest
        self.assertEqual(
            manifest.get_project_by_name(unlocked_proj.name).revision, unlocked_sha)
        self.assertEqual(
            unlocked_proj.remote.refs["feature/donut"].commit.hexsha,
            unlocked_sha)
        self.assertIn(
            "test-tag", unlocked_proj.remote.tags)
        # Tag only pushes tag and updates manifest but doesn't push branch
        self.assertEqual(
            manifest.get_project_by_name(tag_only_proj.name).revision, tag_only_sha)
        self.assertNotEqual(
            tag_only_proj.remote.refs["feature/donut"].commit.hexsha,
            tag_only_sha)
        self.assertIn(
            "test-tag", tag_only_proj.remote.tags)
        # Read only updates manifest but doesn't push branch or tag
        self.assertEqual(
            manifest.get_project_by_name(read_only_proj.name).revision, read_only_sha)
        self.assertNotEqual(
            read_only_proj.remote.refs["feature/donut"].commit.hexsha,
            read_only_sha)
        self.assertNotIn(
            "test-tag", read_only_proj.remote.tags)

    def test_master_push(self):
        self.repo_client.add_branches(["master", "develop"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"})
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"})
        top_dir = self.repo_client.create("master")
        for proj in [unlocked_proj, tag_only_proj, read_only_proj]:
            proj_dir = top_dir / proj.name
            (proj_dir / 'donut').touch()
            proj_repo = Repo(proj_dir)
            proj_repo.git.add(A=True)
            proj_repo.git.commit(m="donut")
            proj_repo.git.tag("test-tag")
        unlocked_sha = Repo(top_dir / unlocked_proj.name).head.commit.hexsha
        tag_only_sha = Repo(top_dir / tag_only_proj.name).head.commit.hexsha
        read_only_sha = Repo(top_dir / read_only_proj.name).head.commit.hexsha

        subprocess.run(
            ["sc", "master", "push"],
            cwd=top_dir, text=True, env=self.env
        )

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        # Unlocked pushes and updates manifest
        self.assertEqual(
            manifest.get_project_by_name(unlocked_proj.name).revision, unlocked_sha)
        self.assertEqual(
            unlocked_proj.remote.refs["master"].commit.hexsha,
            unlocked_sha)
        self.assertIn(
            "test-tag", unlocked_proj.remote.tags)
        # Tag only pushes tag and updates manifest but doesn't push branch
        self.assertEqual(
            manifest.get_project_by_name(tag_only_proj.name).revision, tag_only_sha)
        self.assertNotEqual(
            tag_only_proj.remote.refs["master"].commit.hexsha,
            tag_only_sha)
        self.assertIn(
            "test-tag", tag_only_proj.remote.tags)
        # Read only updates manifest but doesn't push branch or tag
        self.assertEqual(
            manifest.get_project_by_name(read_only_proj.name).revision, read_only_sha)
        self.assertNotEqual(
            read_only_proj.remote.refs["master"].commit.hexsha,
            read_only_sha)
        self.assertNotIn(
            "test-tag", read_only_proj.remote.tags)

    def test_release_push(self):
        self.repo_client.add_branches(["master", "develop", "release/donut"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"})
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"})
        top_dir = self.repo_client.create("release/donut")
        for proj in [unlocked_proj, tag_only_proj, read_only_proj]:
            proj_dir = top_dir / proj.name
            (proj_dir / 'donut').touch()
            proj_repo = Repo(proj_dir)
            proj_repo.git.add(A=True)
            proj_repo.git.commit(m="donut")
            proj_repo.git.tag("test-tag")
        unlocked_sha = Repo(top_dir / unlocked_proj.name).head.commit.hexsha
        tag_only_sha = Repo(top_dir / tag_only_proj.name).head.commit.hexsha
        read_only_sha = Repo(top_dir / read_only_proj.name).head.commit.hexsha

        subprocess.run(
            ["sc", "release", "push", "donut"],
            cwd=top_dir, text=True, env=self.env
        )

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        # Unlocked pushes and updates manifest
        self.assertEqual(
            manifest.get_project_by_name(unlocked_proj.name).revision, unlocked_sha)
        self.assertEqual(
            unlocked_proj.remote.refs["release/donut"].commit.hexsha,
            unlocked_sha)
        self.assertIn(
            "test-tag", unlocked_proj.remote.tags)
        # Tag only pushes tag and updates manifest but doesn't push branch
        self.assertEqual(
            manifest.get_project_by_name(tag_only_proj.name).revision, tag_only_sha)
        self.assertNotEqual(
            tag_only_proj.remote.refs["release/donut"].commit.hexsha,
            tag_only_sha)
        self.assertIn(
            "test-tag", tag_only_proj.remote.tags)
        # Read only updates manifest but doesn't push branch or tag
        self.assertEqual(
            manifest.get_project_by_name(read_only_proj.name).revision, read_only_sha)
        self.assertNotEqual(
            read_only_proj.remote.refs["release/donut"].commit.hexsha,
            read_only_sha)
        self.assertNotIn(
            "test-tag", read_only_proj.remote.tags)

    def test_develop_push(self):
        self.repo_client.add_branches(["master", "develop"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"})
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"})
        top_dir = self.repo_client.create("develop")
        for proj in [unlocked_proj, tag_only_proj, read_only_proj]:
            proj_dir = top_dir / proj.name
            (proj_dir / 'donut').touch()
            proj_repo = Repo(proj_dir)
            proj_repo.git.add(A=True)
            proj_repo.git.commit(m="donut")
            proj_repo.git.tag("test-tag")
        unlocked_sha = Repo(top_dir / unlocked_proj.name).head.commit.hexsha
        tag_only_sha = Repo(top_dir / tag_only_proj.name).head.commit.hexsha
        read_only_sha = Repo(top_dir / read_only_proj.name).head.commit.hexsha

        subprocess.run(
            ["sc", "develop", "push"],
            cwd=top_dir, text=True, env=self.env
        )

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        # Unlocked pushes and updates manifest
        self.assertEqual(
            manifest.get_project_by_name(unlocked_proj.name).revision, unlocked_sha)
        self.assertEqual(
            unlocked_proj.remote.refs["develop"].commit.hexsha,
            unlocked_sha)
        self.assertIn(
            "test-tag", unlocked_proj.remote.tags)
        # Tag only pushes tag and updates manifest but doesn't push branch
        self.assertEqual(
            manifest.get_project_by_name(tag_only_proj.name).revision, tag_only_sha)
        self.assertNotEqual(
            tag_only_proj.remote.refs["develop"].commit.hexsha,
            tag_only_sha)
        self.assertIn(
            "test-tag", tag_only_proj.remote.tags)
        # Read only updates manifest but doesn't push branch or tag
        self.assertEqual(
            manifest.get_project_by_name(read_only_proj.name).revision, read_only_sha)
        self.assertNotEqual(
            read_only_proj.remote.refs["develop"].commit.hexsha,
            read_only_sha)
        self.assertNotIn(
            "test-tag", read_only_proj.remote.tags)

    def test_support_push(self):
        self.repo_client.add_branches(["master", "develop", "support/donut"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"})
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"})
        top_dir = self.repo_client.create("support/donut")
        for proj in [unlocked_proj, tag_only_proj, read_only_proj]:
            proj_dir = top_dir / proj.name
            (proj_dir / 'donut').touch()
            proj_repo = Repo(proj_dir)
            proj_repo.git.add(A=True)
            proj_repo.git.commit(m="donut")
            proj_repo.git.tag("test-tag")
        unlocked_sha = Repo(top_dir / unlocked_proj.name).head.commit.hexsha
        tag_only_sha = Repo(top_dir / tag_only_proj.name).head.commit.hexsha
        read_only_sha = Repo(top_dir / read_only_proj.name).head.commit.hexsha

        subprocess.run(
            ["sc", "support", "push", "donut"],
            cwd=top_dir, text=True, env=self.env
        )

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        # Unlocked pushes and updates manifest
        self.assertEqual(
            manifest.get_project_by_name(unlocked_proj.name).revision, unlocked_sha)
        self.assertEqual(
            unlocked_proj.remote.refs["support/donut"].commit.hexsha,
            unlocked_sha)
        self.assertIn(
            "test-tag", unlocked_proj.remote.tags)
        # Tag only pushes tag and updates manifest but doesn't push branch
        self.assertEqual(
            manifest.get_project_by_name(tag_only_proj.name).revision, tag_only_sha)
        self.assertNotEqual(
            tag_only_proj.remote.refs["support/donut"].commit.hexsha,
            tag_only_sha)
        self.assertIn(
            "test-tag", tag_only_proj.remote.tags)
        # Read only updates manifest but doesn't push branch or tag
        self.assertEqual(
            manifest.get_project_by_name(read_only_proj.name).revision, read_only_sha)
        self.assertNotEqual(
            read_only_proj.remote.refs["support/donut"].commit.hexsha,
            read_only_sha)
        self.assertNotIn(
            "test-tag", read_only_proj.remote.tags)

    def test_hotfix_push(self):
        self.repo_client.add_branches(["master", "develop", "hotfix/donut"])
        unlocked_proj = self.repo_client.add_project()
        tag_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "TAG_ONLY"})
        read_only_proj = self.repo_client.add_project(
            annotations={"GIT_LOCK_STATUS": "READ_ONLY"})
        top_dir = self.repo_client.create("hotfix/donut")
        for proj in [unlocked_proj, tag_only_proj, read_only_proj]:
            proj_dir = top_dir / proj.name
            (proj_dir / 'donut').touch()
            proj_repo = Repo(proj_dir)
            proj_repo.git.add(A=True)
            proj_repo.git.commit(m="donut")
            proj_repo.git.tag("test-tag")
        unlocked_sha = Repo(top_dir / unlocked_proj.name).head.commit.hexsha
        tag_only_sha = Repo(top_dir / tag_only_proj.name).head.commit.hexsha
        read_only_sha = Repo(top_dir / read_only_proj.name).head.commit.hexsha

        subprocess.run(
            ["sc", "hotfix", "push", "donut"],
            cwd=top_dir, text=True, env=self.env
        )

        manifest = ScManifest.from_repo_root(top_dir / ".repo")
        # Unlocked pushes and updates manifest
        self.assertEqual(
            manifest.get_project_by_name(unlocked_proj.name).revision, unlocked_sha)
        self.assertEqual(
            unlocked_proj.remote.refs["hotfix/donut"].commit.hexsha,
            unlocked_sha)
        self.assertIn(
            "test-tag", unlocked_proj.remote.tags)
        # Tag only pushes tag and updates manifest but doesn't push branch
        self.assertEqual(
            manifest.get_project_by_name(tag_only_proj.name).revision, tag_only_sha)
        self.assertNotEqual(
            tag_only_proj.remote.refs["hotfix/donut"].commit.hexsha,
            tag_only_sha)
        self.assertIn(
            "test-tag", tag_only_proj.remote.tags)
        # Read only updates manifest but doesn't push branch or tag
        self.assertEqual(
            manifest.get_project_by_name(read_only_proj.name).revision, read_only_sha)
        self.assertNotEqual(
            read_only_proj.remote.refs["hotfix/donut"].commit.hexsha,
            read_only_sha)
        self.assertNotIn(
            "test-tag", read_only_proj.remote.tags)

    def test_push_fails_on_missing_project(self):
        self.repo_client.add_branches(["master", "develop", "feature/donut"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")
        shutil.rmtree(top_dir / proj.name)

        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.run(
                ["sc", "feature", "push"],
                cwd=top_dir, capture_output=True, check=True, text=True, env=self.env)

        self.assertIn("Repository validation failed", cm.exception.stdout)

    def test_doesnt_push_if_remote_contains_commit(self):
        self.repo_client.add_branches(["master", "develop"])
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(["sc", "feature", "start", "donut"], cwd=top_dir)
        output = subprocess.run(
            ["sc", "feature", "push"],
            cwd=top_dir, capture_output=True, text=True, env=self.env
        )

        self.assertIn("Remote already contains commit. Skipping.", output.stdout)
        self.assertNotIn("feature/donut", [b.name for b in proj.remote.branches])

if __name__ == "__main__":
    unittest.main()
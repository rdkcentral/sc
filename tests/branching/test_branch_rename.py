import subprocess
import unittest

from git import Repo

from .repo_client_creator import RepoTestClientCreator


def _remote_branch_exists(repo: Repo, branch: str) -> bool:
    remote = repo.remotes[0].name
    ref = f"refs/heads/{branch}"
    out = repo.git.ls_remote("--heads", remote, ref)
    return bool(out.strip())


class TestBranchRename(unittest.TestCase):
    def setUp(self):
        self.repo_client = RepoTestClientCreator()

    def tearDown(self):
        self.repo_client.cleanup()

    def test_branch_rename_renames_projects_and_manifest_locally_and_remotely(self):
        self.repo_client.add_branches(
            ["master", "develop", "feature/donut"]
        )
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(
            [
                "sc",
                "branch",
                "rename",
                "feature/donut",
                "feature/pizza",
            ],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")

        self.assertEqual(proj_repo.active_branch.name, "feature/pizza")
        self.assertEqual(manifest_repo.active_branch.name, "feature/pizza")

        self.assertFalse(
            _remote_branch_exists(proj_repo, "feature/donut")
        )
        self.assertTrue(
            _remote_branch_exists(proj_repo, "feature/pizza")
        )
        self.assertFalse(
            _remote_branch_exists(manifest_repo, "feature/donut")
        )
        self.assertTrue(
            _remote_branch_exists(manifest_repo, "feature/pizza")
        )

    def test_branch_rename_local_only_leaves_remote_branches_unchanged(self):
        self.repo_client.add_branches(
            ["master", "develop", "feature/donut"]
        )
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(
            [
                "sc",
                "branch",
                "rename",
                "feature/donut",
                "feature/pizza",
                "--local-only",
            ],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")

        self.assertEqual(proj_repo.active_branch.name, "feature/pizza")
        self.assertEqual(manifest_repo.active_branch.name, "feature/pizza")

        self.assertTrue(
            _remote_branch_exists(proj_repo, "feature/donut")
        )
        self.assertFalse(
            _remote_branch_exists(proj_repo, "feature/pizza")
        )
        self.assertTrue(
            _remote_branch_exists(manifest_repo, "feature/donut")
        )
        self.assertFalse(
            _remote_branch_exists(manifest_repo, "feature/pizza")
        )

    def test_branch_rename_git_only_renames_only_selected_repo(self):
        self.repo_client.add_branches(
            ["master", "develop", "feature/donut"]
        )
        rename_proj = self.repo_client.add_project()
        dummy_proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        subprocess.run(
            [
                "sc",
                "branch",
                "rename",
                "feature/donut",
                "feature/pizza",
                "--git-only",
                "--local-only",
            ],
            cwd=top_dir / rename_proj.name,
            check=True,
        )

        rename_proj_repo = Repo(top_dir / rename_proj.name)
        dummy_proj_repo = Repo(top_dir / dummy_proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")

        self.assertEqual(rename_proj_repo.active_branch.name, "feature/pizza")
        self.assertEqual(dummy_proj_repo.active_branch.name, "feature/donut")
        self.assertEqual(
            manifest_repo.active_branch.name,
            "feature/donut",
        )

    def test_branch_rename_skips_project_not_on_old_branch(self):
        self.repo_client.add_branches(
            ["master", "develop", "feature/donut"]
        )
        proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("develop")

        subprocess.run(
            [
                "sc",
                "branch",
                "rename",
                "feature/donut",
                "feature/pizza",
            ],
            cwd=top_dir,
            check=True,
        )

        proj_repo = Repo(top_dir / proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")

        self.assertEqual(proj_repo.active_branch.name, "develop")
        self.assertEqual(manifest_repo.active_branch.name, "develop")

        self.assertTrue(
            _remote_branch_exists(proj_repo, "feature/donut")
        )
        self.assertFalse(
            _remote_branch_exists(proj_repo, "feature/pizza")
        )

    def test_branch_rename_continues_when_one_project_cannot_be_renamed(self):
        self.repo_client.add_branches(
            ["master", "develop", "feature/donut"]
        )
        first_proj = self.repo_client.add_project()
        second_proj = self.repo_client.add_project()
        top_dir = self.repo_client.create("feature/donut")

        first_repo = Repo(top_dir / first_proj.name)
        first_repo.git.checkout("-b", "feature/pizza")

        subprocess.run(
            [
                "sc",
                "branch",
                "rename",
                "feature/donut",
                "feature/pizza",
                "--local-only",
            ],
            cwd=top_dir,
            check=True,
        )

        second_repo = Repo(top_dir / second_proj.name)
        manifest_repo = Repo(top_dir / ".repo" / "manifests")

        self.assertEqual(first_repo.active_branch.name, "feature/pizza")
        self.assertEqual(second_repo.active_branch.name, "feature/pizza")
        self.assertEqual(
            manifest_repo.active_branch.name,
            "feature/pizza",
        )

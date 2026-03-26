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
"""Module for `sc tag` functionality."""

from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess
import sys

import git
from git import Repo
from repo_library import RepoLibrary
from sc_manifest_parser import ScManifest

from . import common
from .command import Command

logger = logging.getLogger(__name__)

@dataclass
class TagShow(Command):
    """Show information about a particular tag."""
    tag: str

    def run_git_command(self):
        self._git_show(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / ".repo")
        for proj in manifest.projects:
            logger.info(f"Operating in: {self.top_dir / proj.path}")
            if proj.lock_status:
                logger.info(f"GIT_LOCK_STATUS: {proj.lock_status}")
            self._git_show(self.top_dir / proj.path)

            logger.info("-" * 100)

        logger.info(f"Operating on manifest {self.top_dir / '.repo' / 'manifests'}")
        self._git_show(self.top_dir / ".repo" / "manifests")

    def _git_show(self, repo_path: Path):
        try:
            Repo(repo_path)
        except git.NoSuchPathError:
            logger.warning(f"Project path {repo_path} is not a valid directory!")
            return
        except git.InvalidGitRepositoryError:
            logger.warning(f"Project path {repo_path} is not a valid git repository!")
            return

        try:
            out = subprocess.run(
                ["git", "show", self.tag, "--color=always"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            print(out.stdout)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to show tag! {e.stderr}")

@dataclass
class TagList(Command):
    """List all tags."""
    def run_git_command(self):
        self._list_tags(self.top_dir)

    def run_repo_command(self):
        logger.info(f"Tags in manifest: {self.top_dir / '.repo' / 'manifests'}")
        self._list_tags(self.top_dir / '.repo' / 'manifests')

    def _list_tags(self, repo_path: Path):
        subprocess.run(["git", "tag", "-l"], cwd=repo_path, check=False)

@dataclass
class TagCreate(Command):
    """Create a tag."""
    tag: str

    def run_git_command(self):
        subprocess.run(["git", "tag", self.tag], cwd=self.top_dir, check=False)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')

        try:
            common.validate_project_repos(self.top_dir, manifest)
            self._error_if_tag_already_exists(manifest)
        except RuntimeError as e:
            logger.error(e)
            sys.exit(1)

        for proj in manifest.projects:
            logger.info(f"Operating on: {self.top_dir / proj.path}")
            if proj.lock_status == "READ_ONLY":
                logger.info("READ_ONLY, skipping creating tag.")
                continue

            Repo(self.top_dir / proj.path).git.tag(self.tag)
            logger.info(f"Tagged with {self.tag}")

        logger.info(f"Operating on manifest: {self.top_dir / '.repo' / 'manifests'}")
        Repo(self.top_dir / '.repo' / 'manifests').git.tag(self.tag)
        logger.info(f"Tagged with {self.tag}")

    def _error_if_tag_already_exists(self, manifest: ScManifest):
        existing = [
            self.top_dir / proj.path for proj in manifest.projects
            if proj.lock_status != "READ_ONLY" # We aren't tagging READ_ONLY anyway
            and self._tag_exists(self.top_dir / proj.path)
        ]

        if self._tag_exists(self.top_dir / '.repo' / 'manifests'):
            logger.error(f"Tag {self.tag} already exists in the manifest.")
            existing.append(self.top_dir / '.repo' / 'manifests')

        if existing:
            raise RuntimeError(
                "Tag already exists in the following projects:\n" +
                "\n".join(str(p) for p in existing)
            )

    def _tag_exists(self, repo_path: Path):
        return any(t.name == self.tag for t in Repo(repo_path).tags)

@dataclass
class TagRm(Command):
    """Remove a tag."""
    tag: str
    remote: bool

    def run_git_command(self):
        self._delete_tag(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            logger.info(f"Operating on: {self.top_dir / proj.path}")
            if proj.lock_status == "READ_ONLY":
                logger.info("READ_ONLY, skipping removing tag")
                continue

            self._delete_tag(self.top_dir / proj.path, proj.remote)

        logger.info(f"Operating on manifest: {self.top_dir / '.repo' / 'manifests'}")
        self._delete_tag(self.top_dir / '.repo' / 'manifests')

    def _delete_tag(self, repo_path: Path, remote: str = "origin"):
        subprocess.run(["git", "tag", "--delete", self.tag], cwd=repo_path, check=False)
        if self.remote:
            subprocess.run(
                ["git", "push", remote, f":refs/tags/{self.tag}"],
                cwd=repo_path,
                check=False
            )

@dataclass
class TagPush(Command):
    """Push a tag."""
    tag: str

    def run_git_command(self):
        remote = Repo(self.top_dir).remotes[0].name
        self._push_tags(self.top_dir, remote)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            logger.info(f"Operating on: {self.top_dir / proj.path}")
            if proj.lock_status == "READ_ONLY":
                logger.info("READ_ONLY, skipping pushing tags")
                continue

            self._push_tags(self.top_dir / proj.path, proj.remote)

        logger.info(f"Operating on manifest: {self.top_dir / '.repo' / 'manifests'}")
        self._push_tags(self.top_dir / '.repo' / 'manifests')

        logger.info("Push tags complete.")

    def _push_tags(self, repo_path: Path, remote: str = "origin"):
        subprocess.run(
            ["git", "push", remote, f"refs/tags/{self.tag}"],
            cwd=repo_path,
            check=False
        )

@dataclass
class TagCheck(Command):
    """Check all repos for a specific tag."""
    tag: str

    def run_git_command(self):
        self._check_tag(self.top_dir)

    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for proj in manifest.projects:
            logger.info(f"Operating on: {self.top_dir / proj.path}")
            if proj.lock_status == "READ_ONLY":
                logger.info("READ_ONLY, skipping checking tags.")
                continue

            self._check_tag(self.top_dir / proj.path)

        logger.info(f"Operating on manifest: {self.top_dir / '.repo' / 'manifests'}")
        self._check_tag(self.top_dir / '.repo' / 'manifests')

    def _check_tag(self, repo_path: Path):
        subprocess.run(
            ["git", "show-ref", "--tags", "--verify", f"refs/tags/{self.tag}"],
            cwd=repo_path,
            check=False
        )

@dataclass
class TagCheckout(Command):
    tag: str
    force: bool = False
    verify: bool = False

    def run_git_command(self):
        try:
            Repo(self.top_dir).git.checkout(f"refs/tags/{self.tag}")
        except git.GitCommandError as e:
            logger.error(f"Failed to checkout tag: {e}")
            sys.exit(1)

    def run_repo_command(self):
        manifest_repo = Repo(self.top_dir / ".repo" / "manifests")
        manifest_repo.git.fetch("--tags")

        if not any(tag.name == self.tag for tag in manifest_repo.tags):
            logger.error(f"Tag {self.tag} not found in manifest repo!")
            sys.exit(1)

        manifest_repo.git.checkout(f"refs/tags/{self.tag}")
        RepoLibrary.sync(
            self.top_dir,
            force_sync=self.force,
            force_checkout=self.force,
            verify=self.verify,
            detach=True,
            no_prune=True,
            no_manifest_update=True
        )

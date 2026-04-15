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

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET

from git import Repo
from repo_library import RepoLibrary

@dataclass
class Project:
    """The repo here is used to mutate the state of the remote, not the final repo
    that will be created upon RepoTestClientCreator.create()
    """
    name: str
    repo: Repo
    remote: Repo
    groups: str = None
    annotations: dict[str, str] | None = None
    linkfiles: dict[str, str] | None = None
    alt_master: str | None = None
    alt_develop: str | None = None

class RepoTestClientCreator:
    """Create local repo clients with projects to be tested.

    The flow is adding the branches you want, then adding the projects with
    their settings, then running create()
    """
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

        self.man_remote = self._create_temp_remote("manifest")
        self.man_repo = self._create_temp_clone("manifest", self.man_remote)

        self.branches = []
        self.project_settings: list[Project] = []

    def _create_temp_remote(self, name: str) -> Repo:
        path = (self.tmp_path / "remotes" / name)
        path.mkdir(parents = True)
        return Repo.init(path, bare=True)

    def _create_temp_clone(self, name: str, remote: Repo) -> Repo:
        path = (self.tmp_path / "repos" / name)
        path.mkdir(parents = True)
        return Repo.clone_from(remote.working_dir, path)

    def create(self, branch: str, sc_init: bool = True) -> Path:
        """
        Ran after all settings have been applied to create a new repo client
        and return a path to its top_dir.

        Arguments:
            branch (str): The branch the repo client will be checked out on.
            sc_init (bool): Initialise the repo client with sc. Defaults to True.
        """
        self._setup_repositories()

        path = self.tmp_path / str(uuid.uuid4())
        path.mkdir(parents = True)
        RepoLibrary.init(
            uri=Path(self.man_remote.working_dir).as_uri(),
            branch=branch,
            directory=path,
            manifest="manifest.xml",
            no_repo_verify=True,
            quiet=True
        )
        RepoLibrary.sync(directory=path)

        if sc_init:
            subprocess.run(["sc", "init"], cwd=path, capture_output=True)
        return path

    def add_branches(self, branches: list[str]):
        self.branches.extend(branches)

    def add_project(
            self,
            annotations: dict[str, str] = None,
            groups: str | None = None,
            alt_master: str | None = None,
            alt_develop: str | None = None,
        ) -> Project:
        """Each time this is ran adds a project to the repo client."""
        proj_name = str(uuid.uuid4())
        remote_repo = self._create_temp_remote(proj_name)
        proj_repo = self._create_temp_clone(proj_name, remote_repo)

        proj_settings = Project(
            name=proj_name,
            repo=proj_repo,
            remote=remote_repo,
            groups=groups,
            annotations=annotations,
            alt_master=alt_master,
            alt_develop=alt_develop
        )
        self.project_settings.append(proj_settings)
        return proj_settings

    def cleanup(self):
        self.tmp.cleanup()

    def _setup_repositories(self):
        for branch in self.branches:
            self._create_project_branches(branch)
            self._create_manifest_branch(branch)

    def _create_project_branches(self, branch: str):
        for proj in self.project_settings:
            proj.repo.git.checkout("-b", branch)
            path = Path(proj.repo.working_dir) / "README.md"
            path.write_text(branch)
            proj.repo.git.add(A=True)
            proj_branch = self._resolve_project_branch(proj, branch)
            proj.repo.git.commit("--allow-empty", m=proj_branch)
            proj.repo.git.push("-u", "origin", f"HEAD:{proj_branch}")

    def _create_manifest_branch(self, branch: str):
        self.man_repo.git.checkout("-b", branch)
        self._write_manifest(Path(self.man_repo.working_dir) / "manifest.xml")
        self.man_repo.git.add(A=True)
        self.man_repo.git.commit("--allow-empty", m=branch)
        self.man_repo.git.push("-u", "origin", f"HEAD:{branch}")

    def _resolve_project_branch(self, proj: Project, branch: str):
        if branch == "master" and proj.alt_master:
            return proj.alt_master
        if branch == "develop" and proj.alt_develop:
            return proj.alt_develop
        return branch

    def _write_manifest(self, path: Path):
        manifest = ET.Element("manifest")

        ET.SubElement(
            manifest,
            "remote",
            {"name": "sc-testing", "fetch": (self.tmp_path / "remotes").as_uri()}
        )

        ET.SubElement(
            manifest,
            "default",
            {"remote": "sc-testing"}
        )

        for proj in self.project_settings:
            attrs = {
                "name": Path(proj.repo.working_dir).name,
                "revision": proj.repo.active_branch.commit.hexsha,
            }
            if proj.groups:
                attrs["groups"] = proj.groups

            project = ET.SubElement(
                manifest,
                "project",
                attrs
            )

            if proj.annotations:
                for k, v in proj.annotations.items():
                    ET.SubElement(
                        project,
                        "annotation",
                        {"name": k, "value": v}
                    )

            if proj.alt_master:
                ET.SubElement(
                    project,
                    "annotation",
                    {"name": "GIT_FLOW_BRANCH_MASTER", "value": proj.alt_master}
                )

            if proj.alt_develop:
                ET.SubElement(
                    project,
                    "annotation",
                    {"name": "GIT_FLOW_BRANCH_DEVELOP", "value": proj.alt_develop}
                )

        tree = ET.ElementTree(manifest)
        ET.indent(tree, space = "  ")
        tree.write(path, encoding="UTF-8", xml_declaration=True)

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET

from git import Repo
from repo_library import RepoLibrary

@dataclass
class ProjectSettings:
    groups: str = None
    annotations: dict[str, str] | None = None
    linkfiles: dict[str, str] | None = None
    alt_master: str | None = None
    alt_develop: str | None = None

class RepoTestClient:
    def __init__(self, creator: "RepoTestClientCreator", path: Path):
        pass

class RepoTestClientCreator:
    """Create local repo clients with a single project to be tested.

    The flow is to add_branches and settings then
    """
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.man_remote = self._create_temp_remote("manifest")
        self.project_remote = self._create_temp_remote("project")

        self.man_repo = self._create_temp_clone("manifest", self.man_remote)
        self.project_repo = self._create_temp_clone("project", self.project_remote)

        self.branches = []
        self.project_settings = ProjectSettings()

    def _create_temp_remote(self, name: str) -> Repo:
        path = (self.tmp_path / "remotes" / name)
        path.mkdir(parents = True)
        return Repo.init(path, bare=True)

    def _create_temp_clone(self, name: str, remote: Repo) -> Repo:
        path = (self.tmp_path / "repos" / name)
        path.mkdir(parents = True)
        return Repo.clone_from(remote.working_dir, path)

    def add_branch(self, branch: str):
        self.branches.append(branch)

    def add_annotation(self, key: str, value: str):
        if self.project_settings.annotations is None:
            self.project_settings.annotations = {key: value}
        else:
            self.project_settings.annotations[key] = value

    def set_groups(self, groups: str):
        self.project_settings.groups = groups

    def set_alt_master(self, branch: str):
        self.project_settings.alt_master = branch
        self.add_annotation("GIT_FLOW_BRANCH_MASTER", branch)

    def set_alt_develop(self, branch: str):
        self.project_settings.alt_develop = branch
        self.add_annotation("GIT_FLOW_BRANCH_DEVELOP", branch)

    def cleanup(self):
        self.tmp.cleanup()

    def create(self, branch: str, sc_init: bool = True) -> Path:
        for branch in self.branches:
            self._create_branch(branch)

        path = self.tmp_path / str(uuid.uuid4())
        path.mkdir(parents = True)
        RepoLibrary.init(
            uri=Path(self.man_remote.working_dir).as_uri(),
            branch=branch,
            directory=path,
            manifest="manifest.xml",
            no_repo_verify=True
        )
        RepoLibrary.sync(directory=path)
        if sc_init:
            subprocess.run(["sc", "init"], cwd = path)
        return path

    def _create_branch(self, branch: str):
        self.project_repo.git.checkout("-b", branch)
        path = Path(self.project_repo.working_dir) / "README.md"
        path.write_text(branch)
        self.project_repo.git.add(A=True)
        proj_branch = self._resolve_project_branch(branch)
        self.project_repo.git.commit("--allow-empty", m=proj_branch)
        self.project_repo.git.push("-u", "origin", f"HEAD:{proj_branch}")

        self.man_repo.git.checkout("-b", branch)
        self._write_manifest(Path(self.man_repo.working_dir) / "manifest.xml")
        self.man_repo.git.add(A=True)
        self.man_repo.git.commit("--allow-empty", m=branch)
        self.man_repo.git.push("-u", "origin", f"HEAD:{branch}")

    def _resolve_project_branch(self, branch: str):
        if branch == "master" and self.project_settings.alt_master:
            return self.project_settings.alt_master
        if branch == "develop" and self.project_settings.alt_develop:
            return self.project_settings.alt_develop
        return branch

    def _write_manifest(self, path: Path):
        manifest = ET.Element("manifest")

        ET.SubElement(
            manifest,
            "remote",
            {"name": "donut", "fetch": (self.tmp_path / "remotes").as_uri()}
        )

        ET.SubElement(
            manifest,
            "default",
            {"remote": "donut"}
        )

        attrs = {
            "name": Path(self.project_repo.working_dir).name,
            "revision": self.project_repo.active_branch.commit.hexsha,
        }
        if self.project_settings.groups:
            attrs["groups"] = self.project_settings.groups

        project = ET.SubElement(
            manifest,
            "project",
            attrs
        )

        if self.project_settings.annotations:
            for k, v in self.project_settings.annotations.items():
                ET.SubElement(
                    project,
                    "annotation",
                    {"name": k, "value": v}
                )

        tree = ET.ElementTree(manifest)
        ET.indent(tree, space = "  ")
        tree.write(path, encoding="UTF-8", xml_declaration=True)

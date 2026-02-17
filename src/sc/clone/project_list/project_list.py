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

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

import click
from pydantic import BaseModel, ConfigDict, model_validator, ValidationError
import yaml

logger = logging.getLogger(__name__)

class Project(BaseModel):
    """Represents an individual projects configuration."""
    model_config = ConfigDict(extra='forbid')

    name: str
    description: str
    type: str
    branch: str | None = None
    project_repo: str | None = None
    project_prefix: str | None = None
    project_suffix: str | None = None
    manifest: str | None = None
    proc: int = 0
    cache: bool = True
    repo_url: str | None = None
    repo_rev: str | None = None
    no_repo_verify: bool = False
    inherited: str | None = None

    @model_validator(mode='after')
    def check_repo_fields(self):
        if not self.project_repo and not (self.project_prefix and self.project_suffix):
            raise ValueError(
                "Must set either 'project_repo' or both 'project_prefix' and"
                " 'project_suffix'"
            )
        return self

    @property
    def uri(self):
        if self.project_repo:
            return self.project_repo
        if self.project_prefix and self.project_suffix:
            return self.project_prefix + self.project_suffix
        return None

    @property
    def effective_cache(self):
        disable_cache = os.getenv("REPO_CACHE_DISABLED", "").lower() in ("1", "true")
        if disable_cache:
            logger.info("REPO_CACHE_DISABLED env set true. Disabling cache.")

        return self.cache and not disable_cache

class ProjectList:
    """Many project configurations in a hierarchical list."""
    def __init__(self, name: str, path: Path | str):
        self.name = name
        self.path = path
        self.projects = {}

        self._load()

    def _load(self):
        """Populate the ProjectList from the given path."""
        if not Path(self.path).is_file():
            raise IOError(f"Failed to load project list {self.name} from file "
                           f"{self.path} as the path didn't exist!")

        with open(self.path, 'r') as file:
            self.projects = yaml.safe_load(file)

        if not isinstance(self.projects, dict):
            raise ValueError(f"Project list {self.name} is not a mapping!")

        self.projects.pop("project_defaults", None)

    def get_hierarchy(self) -> list[dict]:
        """Returns the hierarchy of the project list

        Returns:
            list[tuple[int, str, bool, str | None]]: Hierarchical structure of projects.
                Each entry in the result is a tuple of:
                (indent_level, name, is_project, description).
        """
        return self._get_projects_hierarchy(self.projects)

    def get_project(self, project_name:str) -> Project | None:
        """Retrieve the information related to a project

        Args:
            project_name: Is a string that represents the name of the project.

        Returns:
            Project: A project configuration.
        """
        project_dict = self._search_projects_by_name(self.projects, project_name)
        if not project_dict:
            return None

        try:
            return Project(name=project_name, **project_dict)
        except ValidationError as e:
            logger.error(f"Invalid project configuration:\n{e}")
            sys.exit(1)

    def _search_projects_by_name(
            self, projects: dict, project_name: str) -> dict[str, str] | None:
        """Recursively searches for a project's configuration in a dictionary.

        Args:
            projects (dict): A dictionary containing all projects.
            project_name (str): The name of the project to find.

        Returns:
            dict | None: The project configuration if found, otherwise None.
        """
        project_dict = projects.get(project_name)

        if project_dict and self._is_project(project_dict):
            return project_dict

        # Recursively search through projects that lack a description
        for sub_project in projects.values():
            if isinstance(sub_project, dict) and not self._is_project(sub_project):
                found_project = self._search_projects_by_name(sub_project, project_name)
                if found_project:
                    return found_project

        return None

    def _get_projects_hierarchy(
            self,
            projects:dict,
            indent:int = 0
        ) -> list[dict]:
        """Recursively builds a list representing the project hierarchy.

        Args:
            projects (dict): Dictionary representing nested projects.
            indent_level (int): Current indentation level for nesting.

        Returns:
            list[tuple[int, str, bool, str | None]]: Hierarchical structure of projects.
                Each entry in the result is a tuple of:
                (indent_level, name, is_project, description).
        """
        result = []
        for name, details in projects.items():
            if not isinstance(details, dict):
                continue

            is_project = self._is_project(details)
            description = details.get('description')
            result.append(
                {
                    "name": name,
                    "indent": indent,
                    "is_project": is_project,
                    "description": description
                }
            )

            if not description:
                result.extend(self._get_projects_hierarchy(details, indent + 1))

        return result

    def _is_project(self, project_dict: dict):
        if project_dict.get('project_repo') or project_dict.get('project_suffix'):
            return True
        return False
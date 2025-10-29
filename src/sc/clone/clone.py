import logging
import os
from pathlib import Path
import re
import shutil
import sys

import click

from .cloners.cloner_runner import ClonerRunner
from .project_list.project_list import ProjectList
from .project_list.project_list_manager import ProjectListManager, ProjectListSource
from sc.config_manager import ConfigManager

from typing import TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from .project_list.project_list import Project

logger = logging.getLogger(__name__)

DEBUG_PROJECT_LIST_PATH = os.getenv("SC_DEBUG_PATH")

class CliOverrides(TypedDict):
    no_tags: bool
    manifest: str | None
    verify: bool

class SCClone:
    """An SC module to clone projects using git-repo by yaml configuration files."""
    def __init__(self):
        self._config_manager = ConfigManager("clone")
        self._project_list_manager = ProjectListManager(
            Path(self._config_manager.config_dir) / 'project_lists'
        )
            
    def clone(
            self, 
            project_name: str, 
            directory: str | None = None, 
            force_overwrite: bool = False,
            no_tags: bool = False, 
            manifest: str | None = None,
            verify: bool = False,
        ):
        """
        Clone all of a projects repositories to a directory.
        
        Args:
            project_name (str): The name of the project to clone. 
            directory (str): The directory the project should clone to. Defaults to None which 
                clones to a folder with the name of the project in the current directory. 
            force_overwrite (bool): Don't ask to delete existing directories. 
                Defaults to False.
            no_tags (bool): Don't clone tags, also turns off caching. Defaults to False.
            manifest (str): Clone with a specific manifest name. Defaults to None.
            verify (bool): Run post-sync hooks without prompting user. RDK projects only.
                Defaults to False.
        """
        project_config = self._resolve_project(project_name)
        target_directory = self._resolve_target_directory(project_name, directory)
        self._prepare_directory(target_directory, force_overwrite)

        logger.info(
            f"Cloning project [{project_config.name}] in directory "
            f"[{target_directory.relative_to(Path.cwd())}]"
        )

        cli_overrides: CliOverrides = {
            'no_tags': no_tags,
            'manifest': manifest,
            'verify': verify
        }

        ClonerRunner().clone(target_directory, project_config, cli_overrides)
    
    def add_project_list(self):
        """Cli method to add new project index to the config."""
        click.echo('Enter a name for this project index:')
        click.echo('Alphanumeric and underscores, no spaces.')
        name = click.prompt('> ')
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            logger.error('Name is not valid (must be alphanumeric and no spaces).')
            sys.exit(1)
        
        if name in self._config_manager.get_config():
            logger.error(f"A index named {name} already exists.")
            sys.exit(1)

        click.echo()
        click.echo('Enter the URL for the project index to add: ')
        click.echo('Please note this should be a URL for the raw file.')
        url = click.prompt('> ')

        click.echo()
        click.echo('Is this URL in a private repository?')
        click.echo('Enter y/n:')
        private_option = click.prompt('> ')

        if private_option == "y":
            click.echo()
            click.echo('Enter the platform your index is hosted on: ')
            click.echo('Possible platforms: ')
            for platform in self._project_list_manager.supported_platforms:
                click.echo(f' - {platform}')
            platform = click.prompt('> ')
            if platform not in self._project_list_manager.supported_platforms:
                logger.error(
                    f"Platform '{platform}' not supported. Supported platforms are: " +
                    ", ".join(self._project_list_manager.supported_platforms)
                )
                sys.exit(1)

            click.echo()
            click.echo('Enter your API Key for this platform: ')
            token = click.prompt('> ')
        
        cache_path = self._project_list_manager.default_dir / f"{name}.yaml"
        source = ProjectListSource(url=url, platform=platform, token=token, path=str(cache_path))

        project_list = self._project_list_manager.load_project_list_from_source(name, source)
        if not project_list:
            sys.exit(1)
        
        self._config_manager.update_config({name: source.model_dump(exclude_none=True)})
        click.echo(f'Added project list {name} to config!')

    def print_projects_hierarchy(self):
        """Prints the project lists, projects, subprojects, and description."""
        config = self._config_manager.get_config()
        project_lists = self._project_list_manager.load_project_lists_from_config(config)
        for plist in project_lists:
            print(self._format_project_tree(plist))
            print()
        
    def _resolve_project(self, project_name: str) -> "Project":
        """
        Resolve a project configuration by name from the available project lists.

        If SC_DEBUG_PATH is set, loads the project list from that path. Otherwise,
        loads project lists from configured sources. If multiple matching projects
        are found, prompts the user to select one. Exits if no matches are found.
        """
        override_path = os.getenv("SC_DEBUG_PATH")
        if override_path:
            project_lists = self._get_overridden_project_list(override_path)
        else:
            config = self._config_manager.get_config()
            project_lists = self._project_list_manager.load_project_lists_from_config(config)

        if not project_lists:
            logger.error("No project lists managed to load! Use sc add-project-list")
            sys.exit(1)

        matches = [
            {"plist": plist.name, "project": project}
            for plist in project_lists
            if (project := plist.get_project(project_name))
        ]

        if not matches:
            for plist in project_lists:
                print(self._format_project_tree(plist))
                print()
            click.secho(f"ERROR: No project {project_name} found", fg="red")
            sys.exit(1)

        if len(matches) == 1:
            return matches[0]["project"]

        click.secho(
            f"WARNING: We found multiple projects with name: {project_name}.", fg="yellow")
        return self._select_project_config(matches)
        
    def _get_overridden_project_list(self, override_path: Path | str):
        logger.warning(f"SC_DEBUG_PATH set using {override_path} for project list!")
        pl = self._project_list_manager.load_local_project_list("DEBUG LIST", override_path)
        return [pl] if pl else [] 
    
    def _select_project_config(
            self,
            project_options: list[dict]
        ) -> "Project":
        while True:
            click.secho(
                "Enter the number next to a lists name to clone its project: ",
                fg="yellow"
            )
            for i, list_name in enumerate(project_options, start=1):
                click.secho(f"{i}: {list_name}", fg="green")

            try:
                chosen_number = int(click.prompt("> "))
                if 1 <= chosen_number <= len(project_options):
                    return project_options[chosen_number - 1]["project"]
                else:
                    click.secho("Invalid input! Try again!", fg="red")
            except ValueError:   
                click.secho("Invalid input! Try again!", fg="red")

    def _resolve_target_directory(self, project_name: str, directory: str):
        return Path.cwd() / directory if directory else Path.cwd() / project_name

    def _prepare_directory(self, directory: Path, force_overwrite: bool):
        def _remove_target(target: Path):
            if target.is_dir():
                shutil.rmtree(target)
            elif target.is_file():
                target.unlink()

        #If empty directory
        if directory.is_dir() and not any(directory.iterdir()):
            return

        if directory == Path.cwd():
            click.secho(
                "ERROR: Current directory not empty!", fg="red"
            )
            sys.exit(1)
        
        if not directory.exists():
            directory.mkdir()
            return

        if force_overwrite:
            click.echo(f"Option [-f] removing dir: [{directory.relative_to(Path.cwd())}]")
            _remove_target(directory)
        else:
            click.secho("WARNING: This directory already exists", fg="yellow")
            click.secho(
                f"Do you want to delete: {directory}, enter (y) or (n):", 
                fg="red"
            )
            user_input = click.prompt("> ")
            if user_input == "y":
                _remove_target(directory)
            else:
                sys.exit(0)
        directory.mkdir()
    
    def _format_project_tree(self, plist: ProjectList) -> str:
        """Returns a stylised tree of the project list."""
        lines = []
        lines.append(click.style(f"{plist.name.upper()}", fg="green", bold=True))
        lines.append("-" * 100)
        for line in plist.get_hierarchy():
            space = "   " * line["indent"]
            if line["is_project"]:
                lines.append(f"{space}{line['name']} --- {line['description']}")
            else:
                colour = ("green", "blue", "magenta")[line["indent"] % 3]
                lines.append(click.style(f"{space}{line['name']}", fg=colour))
        return "\n".join(lines)

    

#!/usr/bin/env python3
#
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

from importlib import metadata
import os
from pathlib import Path

import click

from . import branching_cli, clone_cli, docker_cli, project_cli, sc_logging
from .help import GroupedHelp

CONFIG_DIR = Path(Path.home(), '.sc_config')
CONFIG_PATH = Path(CONFIG_DIR, 'config.yaml')

if os.environ.get("SC_DEBUG") == "1":
    DEBUG_MODE = True
else:
    DEBUG_MODE = False

# Use entry_point instead of pointing directly at cli due to needing to load
# plugins before the click group is ran.
def entry_point():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.touch()

    # Logging
    sc_logging.setup_logging(DEBUG_MODE)
    sc_logging.enable_library_logging("repo_library")
    sc_logging.enable_library_logging("git_flow_library")
    
    # Add commands
    add_commands_under_cli(branching_cli.cli, "Branching")
    add_commands_under_cli(clone_cli.cli, "Clone")
    add_commands_under_cli(docker_cli.cli, "Docker")
    add_commands_under_cli(project_cli.cli, "Project")

    cli()

@click.group(cls=GroupedHelp)
def cli():
    pass

@cli.command()
def version():
    """Display SC Version."""
    click.echo(metadata.version("sc"))

def add_commands_under_cli(other_cli: click.Group, section: str | None):
    """Add 

    Args:
        other_cli (click.Group): _description_
        section (str | None): _description_
    """    
    for cmd in other_cli.commands.values():
        if section:
            setattr(cmd, "section", section)
        cli.add_command(cmd)

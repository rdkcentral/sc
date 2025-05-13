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

from importlib import metadata, import_module
import logging
import os
from pathlib import Path
import pkg_resources
import sys

import click
from rich.logging import RichHandler 

CONFIG_DIR = Path(Path.home(), '.sc_config')
CONFIG_PATH = Path(CONFIG_DIR, 'config.yaml')

# Use entry_point instead of pointing directly at cli due to needing to load
# plugins before the click group is ran.
def entry_point():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.touch()
    load_plugins()
    cli()

@click.group()
def cli():
    pass

@cli.command()
def version():
    """Display SC Version."""
    click.echo(metadata.version("sc"))

def load_plugins():
    """Load plugins with 'sc-' prefix and merge their CLI commands"""
    for dist in pkg_resources.working_set:
        if dist.project_name.startswith("sc-"):
            try:
                module_name = dist.project_name.replace('-','_')
                plugin_module = import_module(module_name)

                if hasattr(plugin_module, "cli") and isinstance(plugin_module.cli, click.Group):
                    for cmd_name, cmd in plugin_module.cli.commands.items():
                        if cmd_name not in cli.commands:
                            cli.commands[cmd_name] = cmd
                        else:
                            click.secho(
                                f"ERROR: Command {cmd_name} in two plugins!", fg="red")
                            sys.exit(1)
                    setup_logging_for_plugin(dist.project_name, module_name)
            except Exception as e:
                print(e)

def setup_logging_for_plugin(plugin_name:str, module_name: str):
    """Setup the logging for a plugin by its module name.
    
    This will automatically pick up any loggers = logging.getLogger(__name__) in the 
    loaded plugin.

    Args:
        plugin_name (str): The name of the plugin to be added to the start of logs.
        module_name (str): The actual name of the plugins module separated so name can 
            have hyphens while module name needs underscores.
    """
    plugin_logger = logging.getLogger(module_name)
    formatter = ScLoggerFormatter(plugin_name)

    handler = RichHandler(show_time=False, show_path=False)
    handler.setFormatter(formatter)
    plugin_logger.addHandler(handler)

class ScLoggerFormatter(logging.Formatter):
    """Custom formatter that injects a plugin name into each log record."""
    DEFAULT_FMT = '[%(plugin)s] %(message)s'
    DEBUG_FMT = '[%(plugin)s] %(name)s: %(message)s'

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        super().__init__()

    def format(self, record):
        record.plugin = self.plugin_name
        if os.environ.get("SC_DEBUG") == 1:
            self._style._fmt = self.DEBUG_FMT
        else:
            self._style._fmt = self.DEFAULT_FMT
        return super().format(record)
    
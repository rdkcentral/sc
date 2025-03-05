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

import click

CONFIG_DIR = Path(Path.home(), '.sc_config')
CONFIG_PATH = Path(CONFIG_DIR, 'config.yaml')

logger = logging.getLogger("sc")

# Use entry_point instead of pointing directly at cli due to needing to load
# plugins before the click group is ran.
def entry_point():
    _setup_logging()

    logger.debug(f"NAME = {__name__}")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.touch()
    _load_plugins()
    cli()

@click.group()
def cli():
    pass

@cli.command()
def version():
    """Display SC Version."""
    click.echo(metadata.version("sc"))

def _load_plugins():
    """Load plugins with 'sc-' prefix and merge their CLI commands"""
    for dist in pkg_resources.working_set:
        if dist.project_name.startswith("sc-"):
            try:
                logger.debug(f"Importing {dist.project_name}")
                plugin_module = import_module(dist.project_name.replace('-','_'))

                if hasattr(plugin_module, "cli") and isinstance(plugin_module.cli, click.Group):
                    cli.add_command(plugin_module.cli, name=dist.project_name.replace("sc-", ""))
            except Exception as e:
                logger.warning(f"Failed to import {dist.project_name}:", exc_info=True)

def _setup_logging():
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    
    handler = logging.StreamHandler()

    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

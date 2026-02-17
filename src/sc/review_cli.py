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

import click

from .review import main

@click.group()
def cli():
    pass

@cli.command()
def review():
    """Add commit/PR information to your ticket."""
    main.review()

@cli.command()
def add_git_instance():
    """Add a VCS instance for sc review."""
    main.add_git_instance()

@cli.command()
def add_ticketing_instance():
    """Add a ticketing instance for sc review."""
    main.add_ticketing_instance()
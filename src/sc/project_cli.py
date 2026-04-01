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

import logging

import click

from sc.branching import SCBranching

logger = logging.getLogger(__name__)

@click.group()
def cli():
    pass

@cli.command()
def init():
    """Initialise for branching commands."""
    SCBranching.init()

@cli.command()
def clean():
    """Clean all modules. (git clean -fdx)."""
    SCBranching.clean()

@cli.command()
def status():
    """Show the working tree status."""
    SCBranching.status()

@cli.command()
def reset():
    """Clean and Reset all modules to remote manifest. (git reset --hard REMOTE)"""
    SCBranching.reset()

@cli.group()
def tag():
    """Commands surrounding tags."""
    pass

@tag.command()
def list():
    """List tags in manifest or git repo."""
    SCBranching.tag_list()

@tag.command()
@click.argument("tag")
def show(tag):
    """Show information about a tag in all repos."""
    SCBranching.tag_show(tag)

@tag.command()
@click.argument("tag")
def create(tag):
    """Create a tag in all non READ_ONLY repos."""
    SCBranching.tag_create(tag)

@tag.command()
@click.argument("tag")
@click.option('-r', '--remote', is_flag=True, help="Remove in remotes as well as local.")
def rm(tag, remote):
    """Remove a tag in all non READ_ONLY repos."""
    SCBranching.tag_rm(tag, remote)

@tag.command()
@click.argument("tag")
def push(tag):
    """Push given tag in all non READ_ONLY repos."""
    SCBranching.tag_push(tag)

@tag.command()
@click.argument("tag")
def check(tag):
    """Check if a tag exists on all non READ_ONLY repos."""
    SCBranching.tag_check(tag)

@cli.group()
def show():
    """Show information about a project."""
    pass

@show.command()
def branch():
    """Show the current status of branching."""
    SCBranching.show_branch()

@show.command()
def repo_flow_config():
    """Show git flow config for all projects."""
    SCBranching.show_repo_flow_config()

@show.command()
def log():
    SCBranching.show_log()

@show.command()
@click.argument("tag")
def tag(tag):
    """Show information about a tag."""
    SCBranching.tag_show(tag)

@show.command()
def tags():
    """List tags on the manifest."""
    SCBranching.tag_list()

@show.command()
@click.argument("group", required=False)
def group(group):
    """List groups or show information about a group."""
    SCBranching.group_show(group)
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

from sc.branching import SCBranching

@click.group()
def cli():
    pass

@cli.command()
def init():
    """Initialise project for branching commands."""
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

@tag.command(name="list")
def tag_list():
    """List tags in manifest or git repo."""
    SCBranching.tag_list()

@tag.command(name="show")
@click.argument("tag")
def tag_show(tag):
    """Show information about a tag in all repos."""
    SCBranching.tag_show(tag)

@tag.command(name="create")
@click.argument("tag")
def tag_create(tag):
    """Create a tag in all non READ_ONLY repos."""
    SCBranching.tag_create(tag)

@tag.command(name="rm")
@click.argument("tag")
@click.option('-r', '--remote', is_flag=True, help="Remove in remotes as well as local.")
def tag_rm(tag, remote):
    """Remove a tag in all non READ_ONLY repos."""
    SCBranching.tag_rm(tag, remote)

@tag.command(name="push")
@click.argument("tag")
def tag_push(tag):
    """Push given tag in all non READ_ONLY repos."""
    SCBranching.tag_push(tag)

@tag.command(name="check")
@click.argument("tag")
def tag_check(tag):
    """Check if a tag exists on all non READ_ONLY repos."""
    SCBranching.tag_check(tag)


@cli.group()
def show():
    """Show information about a project."""
    pass

@show.command(name="branch")
def show_branch():
    """Show the current status of branching."""
    SCBranching.show_branch()

@show.command(name="repo_flow_config")
def show_repo_flow_config():
    """Show git flow config for all projects."""
    SCBranching.show_repo_flow_config()

@show.command(name="log")
def show_log():
    """Show git log for all projects."""
    SCBranching.show_log()

@show.command(name="tag")
@click.argument("tag")
def show_tag(tag):
    """Show information about a tag."""
    SCBranching.tag_show(tag)

@show.command(name="tags")
def show_tags():
    """List tags on the manifest."""
    SCBranching.tag_list()

@show.command(name="group")
@click.argument("group", required=False)
def show_group(group):
    """List groups or show information about a group."""
    SCBranching.group_show(group)


@cli.group()
def group():
    """Commands on a group of projects in the manifest."""

@group.command(name="checkout")
@click.argument("group")
@click.argument("branch")
def group_checkout(group, branch):
    """Checkout all projects in a group to a branch."""
    SCBranching.group_checkout(group, branch)

@group.command(name="cmd")
@click.argument("group")
@click.argument("command", nargs=-1)
def group_cmd(group, command):
    """Run a command in all projects in a group."""
    SCBranching.group_cmd(group, command)

@group.command(name="fetch")
@click.argument("group")
def group_fetch(group):
    """Git fetch projects in a group."""
    SCBranching.group_fetch(group)

@group.command(name="pull")
@click.argument("group")
def group_pull(group):
    """Pull projects in a group."""
    SCBranching.group_pull(group)

@group.command(name="push")
@click.argument("group")
def group_push(group):
    """Push projects in a group."""
    SCBranching.group_push(group)

@group.command(name="show")
@click.argument("group", required=False)
def group_show(group):
    """List groups or show information about a group."""
    SCBranching.group_show(group)

@group.command(name="tag")
@click.argument("group")
@click.argument("tag")
@click.option("-m", "--message", help="Add a message to the tags.")
@click.option("-p", "--push", is_flag=True, help="Push the tags to remote.")
def group_tag(group, tag, message, push):
    """Tag all projects in a group."""
    SCBranching.group_tag(group, tag, message, push)

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
from sc.branching.branch import BranchType

@click.group()
def cli():
    pass

# Feature branch commands
@cli.group()
def feature():
    """Feature branch subcommands"""
    pass

@feature.command()
@click.argument('name')
def start(name: str):
    """Creates a new feature/<branch> from the develop branch, and switched to."""
    SCBranching.start(BranchType.FEATURE, name, BranchType.DEVELOP)


@feature.command()
@click.argument('name')
@click.option("-f", "--force", is_flag=True, help="Force checkout.")
@click.option("-v", "--verify", is_flag=True, help="Run hooks without prompting.")
def checkout(name, force, verify):
    """Checkout the feature branch"""
    SCBranching.checkout(BranchType.FEATURE, name, force, verify)


@feature.command()
@click.argument('name', required=False)
def pull(name):
    """Pull the remote branch"""
    SCBranching.pull(BranchType.FEATURE, name)


@feature.command()
@click.argument('name', required=False)
@click.option("-m", "--message", help="Manifest commit message.")
def push(name, message):
    """Push to remote, if a Repo project updates the manifest."""
    SCBranching.push(BranchType.FEATURE, name, message)


@feature.command()
@click.argument('name', required=False)
def finish(name):
    """Merge the feature branch into develop"""
    SCBranching.finish(BranchType.FEATURE, name)

@feature.command()
def list():
    """List feature branches."""
    SCBranching.list(BranchType.FEATURE)

# Develop branch commands
@cli.group()
def develop():
    """Develop branch subcommands"""
    pass


@develop.command()
def pull():
    """Pull from develop branch."""
    SCBranching.pull(BranchType.DEVELOP)


@develop.command()
@click.option("-m", "--message", help="Manifest commit message.")
def push(message):
    """Push develop branch to remote, if a Repo project updates the manifest."""
    SCBranching.push(BranchType.DEVELOP, None, message)


@develop.command()
@click.option("-f", "--force", is_flag=True, help="Force checkout.")
@click.option("-v", "--verify", is_flag=True, help="Run hooks without prompting.")
def checkout(force, verify):
    """Checkout a develop branch."""
    SCBranching.checkout(BranchType.DEVELOP, None, force, verify)


# Master branch commands
@cli.group()
def master():
    """Master branch subcommands"""
    pass


@master.command()
def pull():
    """Pull from master branch."""
    SCBranching.pull(BranchType.MASTER)


@master.command()
@click.option("-m", "--message", help="Manifest commit message.")
def push(message):
    """Push master branch to remote, if a Repo project updates the manifest."""
    SCBranching.push(BranchType.MASTER, None, message)


@master.command()
@click.option("-f", "--force", is_flag=True, help="Force checkout.")
@click.option("-v", "--verify", is_flag=True, help="Run hooks without prompting.")
def checkout(force, verify):
    """Checkout the master branch."""
    SCBranching.checkout(BranchType.MASTER, None, force, verify)


# Release branch commands
@cli.group()
def release():
    """Manage release branches."""
    pass

@release.command()
@click.argument('version')
def start(version: str):
    """Create a new release branch."""
    SCBranching.start(BranchType.RELEASE, version, BranchType.DEVELOP)


@release.command()
@click.argument('name', required=False)
def finish(name):
    """Merge release branch."""
    SCBranching.finish(BranchType.RELEASE, name)


@release.command()
@click.argument('name')
def pull(name: str | None):
    """Pull down the latest changes from the remote branch."""
    SCBranching.pull(BranchType.RELEASE, name)

@release.command()
@click.argument('name', required=False)
@click.option("-m", "--message", help="Manifest commit message.")
def push(name: str, message):
    """Push release branch to remote, if a Repo project updates the manifest."""
    SCBranching.push(BranchType.RELEASE, name, message)

@release.command()
@click.argument('name')
@click.option("-f", "--force", is_flag=True, help="Force checkout.")
@click.option("-v", "--verify", is_flag=True, help="Run hooks without prompting.")
def checkout(name, force, verify):
    """Checkout the release branch by tag name"""
    SCBranching.checkout(BranchType.RELEASE, name, force, verify)

@release.command()
def list():
    """List release branches."""
    SCBranching.list(BranchType.RELEASE)

# Hotfix branch commands
@cli.group()
def hotfix():
    """Hotfix branch subcommands"""
    pass

@hotfix.command()
@click.argument('version')
@click.argument('base')
def start(version: str, base: str):
    """Create a new hotfix branch from a source branch, named <release_prefix><major>.<minor>.<bugfix>"""
    SCBranching.start(BranchType.HOTFIX, version, base)


@hotfix.command()
@click.argument('name')
@click.option("-f", "--force", is_flag=True, help="Force checkout.")
@click.option("-v", "--verify", is_flag=True, help="Run hooks without prompting.")
def checkout(name, force, verify):
    """Checkout the hotfix tag by name"""
    SCBranching.checkout(BranchType.HOTFIX, name, force, verify)


@hotfix.command()
@click.argument('name', required=False)
@click.option("-m", "--message", help="Manifest commit message.")
def push(name, message):
    """Push to remote, if it's a Repo project updates the manifest."""
    SCBranching.push(BranchType.HOTFIX, name, message)


@hotfix.command()
@click.argument('name')
def pull(name: str | None):
    """Pull from the remote hotfix branch"""
    SCBranching.pull(BranchType.HOTFIX, name)


@hotfix.command()
@click.argument('name', required=False)
@click.argument('base', required=False)
def finish(name, base):
    """Merge this hotfix branch."""
    SCBranching.finish(BranchType.HOTFIX, name, base)

@hotfix.command()
def list():
    """List hotfix branches."""
    SCBranching.list(BranchType.HOTFIX)

# Support branch commands
@cli.group()
def support():
    """Support branch subcommands"""
    pass

@support.command()
@click.argument('version')
@click.argument('base')
def start(version: str, base: str):
    """Start a support branch."""
    SCBranching.start(BranchType.SUPPORT, version, base)


@support.command()
@click.argument('name', required=False)
@click.option("-m", "--message", help="Manifest commit message.")
def push(name, message):
    """Push to remote, if it's a Repo project updates."""
    SCBranching.push(BranchType.SUPPORT, name, message)


@support.command()
@click.argument('name')
def pull(name: str | None):
    """Pull from the remote support branch"""
    SCBranching.pull(BranchType.SUPPORT, name)

@support.command()
def list():
    """List support branches."""
    SCBranching.list(BranchType.SUPPORT)

@support.command()
@click.argument('name')
@click.option("-f", "--force", is_flag=True, help="Force checkout.")
@click.option("-v", "--verify", is_flag=True, help="Run hooks without prompting.")
def checkout(name, force, verify):
    """Checkout a support branch."""
    SCBranching.checkout(BranchType.SUPPORT, name, force, verify)

if __name__ == '__main__':
    cli()

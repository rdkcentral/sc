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
from sc.branching.branch import BranchType

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
    SCBranching.sc_clean()

@cli.command()
def status():
    """Show the working tree status."""
    SCBranching.sc_status()



@cli.command()
def reset():
    """Clean and Reset all modules to remote manifest. (git reset --hard REMOTE)"""
    SCBranching.sc_reset()



@cli.command()
def build():
    """Executes build related commands specified in a yaml file."""
    pass

@cli.command()
@click.option("-n", "--no-checkout", is_flag=True, help="Do not checkout the branch.")
@click.option("-b", "--force-broken", is_flag=True, help="Do not checkout the branch.")
@click.option("-s", "--force-sync", is_flag=True, help="Do not checkout the branch.")
def sync(no_checkout, force_broken, force_sync):
    """Perform sync, and re-checkout branch"""
    pass


# Feature branch commands
@cli.group()
def feature():
    """Feature branch subcommands"""
    pass

@feature.command()
@click.argument('name')
@click.argument('base', default=BranchType.DEVELOP)
def start(name: str, base: str):
    """Creates a new feature/<branch> from the develop branch, and switched to."""
    SCBranching.start(BranchType.FEATURE, name, base)


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
def push(name):
    """Push to remote, if a repo project updates the manifest with the lastest commits."""
    SCBranching.push(BranchType.FEATURE, name)


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
def push():
    """Push develop branch to remote, if a repo project updates the manifest with the lastest commits."""
    SCBranching.push(BranchType.DEVELOP)


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
def push():
    """Push master branch to remote, if a repo project updates the manifest with the lastest commits."""
    SCBranching.push(BranchType.MASTER)


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
@click.argument('tag_name', required=False)
def finish(tag_name):
    """Merge release branch master and develop and tag it with the `<tag name>` provided."""
    SCBranching.finish(BranchType.RELEASE, tag_name)


@release.command()
def pull():
    """Pull down the latest changes from the remote branch."""
    SCBranching.pull(BranchType.RELEASE)


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
@click.argument('base', default=BranchType.RELEASE)
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
def push(name):
    """Push to remote, if it's a repo project also updates the manifest with the lastest commits."""
    SCBranching.push(BranchType.HOTFIX, name)


@hotfix.command()
@click.argument('name')
def pull(name: str | None):
    """Pull from the remote hotfix branch"""
    SCBranching.pull(BranchType.HOTFIX, name)


@hotfix.command()
@click.argument('tag_name', required=False)
@click.argument('base', required=False)
def finish(tag_name, base):
    """Merge this hotfix branch if it's support branch and tagged"""
    logger.info(f"tag_name {tag_name}, base {base}")
    SCBranching.finish(BranchType.HOTFIX, tag_name, base)

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
@click.argument('base', default = BranchType.RELEASE)
def start(version: str, base: str):
    """Start a support branch."""
    SCBranching.start(BranchType.SUPPORT, version, base)


@support.command()
@click.argument('name', required=False)
def push(name):
    """Push to remote, if it's a repo project also updates the manifest with the lastest commits."""
    SCBranching.push(BranchType.SUPPORT, name)


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

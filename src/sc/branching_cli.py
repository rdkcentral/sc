import logging

import click

from sc.branching import SCBranching
from sc.branching.branch import BranchType

logger = logging.getLogger(__name__)

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
    """Checkout the develop branch"""
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


# Support branch commands
@cli.group()
def support():
    """Support branch subcommands"""
    pass


@support.command()
@click.argument('version')
@click.argument('base', default = BranchType.RELEASE)
def start(version: str, base: str):
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


if __name__ == '__main__':
    cli()

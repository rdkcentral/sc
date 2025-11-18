
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
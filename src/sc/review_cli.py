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
import click

from .review import main 

@click.group()
def cli():
    pass

@cli.command()
def review():
    main.review()

@cli.command()
def add_vcs_instance():
    main.add_vcs_instance()

@cli.command()
def add_ticketing_instance():
    main.add_ticketing_instance()
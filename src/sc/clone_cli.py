#!/usr/bin/env python3
import click

from sc.clone import SCClone

@click.group
def cli():
    pass

@cli.command()
@click.argument('project', required=False)
@click.argument('directory', required=False)
@click.option('-r', '--rev', help='Clone a revision. Accepts branch name, tag name, or full SHA.')
@click.option('-n', '--no-tags', is_flag=True, help='Clone without tags.')
@click.option('-m', '--manifest', help='Clone with specific manifest name.')
@click.option('-f', '--force', is_flag=True, help="Automatically overwrite directory.")
@click.option('-v', '--verify', is_flag=True, help='RDK projects only, run post-sync-hooks without prompts.')
@click.pass_context
def clone(
        ctx, 
        project: str | None, 
        directory: str | None, 
        rev: str | None,
        no_tags: bool,
        manifest: str | None, 
        force: bool,
        verify: bool,
    ):
    """Clone groups of repositories from a config."""
    if project:
        SCClone().clone(
            project_name=project, 
            directory=directory, 
            rev=rev,
            no_tags=no_tags, 
            manifest=manifest,
            force_overwrite=force,
            verify=verify,
        )
    else:
        click.secho("Please specify a project or subcommand.", fg="red", bold=True)
        click.echo(ctx.get_help())
        SCClone().print_projects_hierarchy()

@cli.command()
def add_project_list():
    """Add new project lists to sc-clone."""
    SCClone().add_project_list()

if __name__ == '__main__':
    cli()
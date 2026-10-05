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
"""Manifest-based workspace navigation and shell integration."""

from pathlib import Path
import re

import click
from lxml.etree import XMLSyntaxError
from sc_manifest_parser import ScManifest


@click.group()
def cli():
    pass


def _workspace_root():
    current = Path.cwd()
    for directory in (current, *current.parents):
        if (directory / ".repo").is_dir():
            return directory
    raise click.ClickException(f"'{current}' does not belong to a repo workspace.")


def _describe(project, verbose=False):
    click.echo(
        f"[ {project.path} ] [ {project.name} ] "
        f"LOCK_STATUS: [{project.lock_status or 'NORMAL'}]", err=True
    )
    if verbose:
        for label, value in (("REPO_PROJECT", project.name),
                             ("REPO_PATH", project.path),
                             ("REPO_REMOTE", project.remote),
                             ("REPO_RREV", project.revision)):
            click.echo(f"{label}: [ {value or ''} ]", err=True)
        for annotation in project.search_children("annotation"):
            click.echo(f"{annotation.name}: [ {annotation.value} ]", err=True)


@cli.command()
@click.argument("pattern", required=False)
@click.option("-l", "--l", "--list", "list_projects", is_flag=True,
              help="List all projects on stderr; optionally navigate to PATTERN.")
@click.option("-v", "--v", "--verbose", "verbose", is_flag=True,
              help="Show matched project attributes and annotations on stderr.")
@click.option("-w", "--w", "--word", "word", is_flag=True,
              help="Require whole-word matches, as with the original go.sh -w.")
def go(pattern, list_projects, verbose, word):
    """Print a project path, or the special destinations root and manifest.

    PATTERN is a case-insensitive regular expression matching project names,
    paths, or directory names. An exact name or path takes precedence.
    """
    if not pattern and not list_projects:
        raise click.UsageError("Supply a project pattern, root, manifest, or --list.")
    root = _workspace_root()
    destination = None
    if pattern in ("root", "manifest"):
        destination = root if pattern == "root" else root / ".repo" / "manifests"
    if destination is None or list_projects:
        try:
            projects = ScManifest.from_repo_root(root / ".repo").projects
        except (OSError, ValueError, XMLSyntaxError) as error:
            raise click.ClickException(f"Cannot read workspace manifest: {error}") from error
        if list_projects:
            for project in projects:
                _describe(project, verbose)
        if not pattern:
            return
        if destination is None:
            try:
                expression = re.compile(
                    rf"(?<!\w)(?:{pattern})(?!\w)" if word else pattern,
                    re.IGNORECASE,
                )
            except re.error as error:
                raise click.BadParameter(str(error), param_hint="PATTERN") from error
            exact = []
            matches = []
            for project in projects:
                names = (project.name, project.path, Path(project.path).name)
                if any(pattern.casefold() == name.casefold() for name in names):
                    exact.append(project)
                if any(expression.search(name) for name in names):
                    matches.append(project)
            matches = exact or matches
            if not matches:
                raise click.ClickException(f"No project matches '{pattern}'.")
            if len(matches) > 1:
                for project in matches:
                    _describe(project)
                raise click.ClickException(
                    f"Multiple projects match '{pattern}'; use a full project name or path."
                )
            project = matches[0]
            if verbose and not list_projects:
                _describe(project, verbose=True)
            destination = root / project.path
    if not destination.is_dir():
        raise click.ClickException(f"Directory does not exist: {destination}")
    click.echo(str(destination))


@cli.command("go-init")
@click.argument("shell", type=click.Choice(["bash", "zsh"]), default="bash")
def go_init(shell):
    """Print shell integration (defaults to bash).

    Add eval "$(sc go-init bash)" to ~/.bashrc, or
    eval "$(sc go-init zsh)" to ~/.zshrc.
    """
    # Keep user Zsh options from changing the function's behavior. -L restores
    # those options when the function returns.
    shell_setup = "    emulate -L zsh;\n" if shell == "zsh" else ""
    click.echo('''unalias go 2>/dev/null || :;
function go() {
''' + shell_setup + '''    local destination;
    case " $* " in
        *" --help "*) command sc go "$@"; return $? ;;
    esac;
    destination="$(command sc go "$@")" || return $?;
    if [ -n "$destination" ]; then
        builtin cd -- "$destination";
    fi;
}''')

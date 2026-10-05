<div align="center">

# Software Control (SC)
![language](https://img.shields.io/badge/language-python-239120)
![OS](https://img.shields.io/badge/OS-linux%2C%20macOS-0078D4)

SC is a collection of CLI tools, centered around version control and docker workflow.

</div>

## Table of Contents
- [Requirements](#requirements)
- [Installing](#installing)
- [Workspace navigation](#workspace-navigation)

## Requirements

* Install Python 3.10+
* Googles git-repo tool, install instructions [here.](https://gerrit.googlesource.com/git-repo)
* The docker engine must be installed.
    * Installation instructions can be found [here.](https://docs.docker.com/engine/install/)
* Access to the docker engine
    * Access to the docker engine, could require privileged permissions, on linux it requires the user to be part of the docker group. See installation instructions above for more about this.

## Installing

`pip` is the default Python package manager, but Ubuntu 23.04+ prevents global installs. Rather than relying on virtual environments, we recommend `uv` for faster performance and simpler global CLI tool management.

### pip

```shell
pip install git+https://github.com/rdkcentral/sc.git@main
```

### uv

See the uv install guide [here.](https://docs.astral.sh/uv/getting-started/installation/)

```shell
# Install sc as a global tool
uv tool install git+https://github.com/rdkcentral/sc.git@main

sc --help

# Update sc to latest
uv tool upgrade sc

# Uninstall sc
uv tool uninstall sc
```

## Workspace navigation

For Bash, add this to `~/.bashrc`, after any old `go` alias or function setup:

```bash
eval "$(sc go-init bash)"
```

For Zsh, add this to `~/.zshrc`:

```zsh
eval "$(sc go-init zsh)"
```

Start a new shell or run the corresponding line in your current shell.
`sc go-init` without a shell argument still defaults to Bash.

From anywhere inside a repo workspace:

```bash
go project_name       # Navigate by manifest project name or checkout path
go root               # Workspace root
go manifest           # .repo/manifests
go -l                 # List projects without changing directory
go -v project_name    # Navigate and show manifest attributes/annotations
go -w project_name    # Whole-word search
```

Searches use case-insensitive regular expressions. Exact project names, paths,
or directory names take precedence over partial matches. Ambiguous searches
show the candidates and fail; use a full name or path to select one.
Missing checkouts and failed searches leave your current directory unchanged.

`sc go project_name` prints only the destination path to stdout, so it can also
be used as `cd "$(sc go project_name)"`. Listings, verbose output, and errors go
to stderr. The commands use `sc-manifest-parser`, including its manifest include
and remove-project handling; they do not invoke `repo forall` or use `~/.go.var`.
The old script's internal `--find` option is no longer needed.

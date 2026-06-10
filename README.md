<div align="center">

# Software Control (SC)
![language](https://img.shields.io/badge/language-python-239120)
![OS](https://img.shields.io/badge/OS-linux%2C%20macOS-0078D4)

SC is a collection of CLI tools, centered around version control and docker workflow.

</div>

## Table of Contents
- [Requirements](#requirements)
- [Installing](#installing)

## Requirements

* Install Python 3.10+
* Googles git-repo tool, install instructions [here.](https://gerrit.googlesource.com/git-repo)
* The docker engine must be installed.
    * Installation instructions can be found [here.](https://docs.docker.com/engine/install/)
* Access to the docker engine
    * Access to the docker engine, could require privileged permissions, on linux it requires the user to be part of the docker group. See installation instructions above for more about this.

## Installing

`pip` is the default Python package manager, but Ubuntu 23.04+ prevents global installs. We recommend `uv` (fastest) or `pipx` (isolated global tools) instead of plain `pip`.

| Method | When to use | Notes |
| ------ | ----------- | ----- |
| `uv`   | Default choice | Fastest install / upgrade, simplest global CLI tool management |
| `pipx` | Existing pipx workflow | Each tool gets its own isolated virtualenv automatically |
| `pip`  | Already in a venv | Direct, but blocked by PEP 668 on modern distros for global installs |

### uv (recommended)

See the [uv install guide](https://docs.astral.sh/uv/getting-started/installation/).

```shell
# Install sc as a global tool
uv tool install git+https://github.com/rdkcentral/sc.git@main

sc --help

# Update sc to the latest main
uv tool upgrade sc

# Pin to a specific release (recommended for shared / CI hosts)
uv tool install git+https://github.com/rdkcentral/sc.git@1.0.15

# Uninstall sc
uv tool uninstall sc
```

### pipx

See the [pipx install guide](https://pipx.pypa.io/stable/installation/).

```shell
# Install sc as a global isolated tool
pipx install git+https://github.com/rdkcentral/sc.git@main

sc --help

# Update sc to the latest main
pipx upgrade sc

# Pin to a specific release
pipx install --force git+https://github.com/rdkcentral/sc.git@1.0.15

# Uninstall sc
pipx uninstall sc
```

### pip

Only inside an activated virtualenv:

```shell
pip install git+https://github.com/rdkcentral/sc.git@main
```

### Check your install

```shell
sc --version          # show version
sc docker --help      # confirm docker subcommand is wired up
```

If you've installed previously and the version looks out of date, check
which install path is on `PATH`:

```shell
which sc
# uv:    ~/.local/share/uv/tools/sc/bin/sc
# pipx:  ~/.local/share/pipx/venvs/sc/bin/sc → ~/.local/bin/sc
# pip:   inside your virtualenv
```

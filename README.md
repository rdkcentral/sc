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
    * Installation instructions can be found [here](https://docs.docker.com/engine/install/)
* Access to the docker engine
    * Access to the docker engine, could require privileged permissions, on linux it requires the user to be part of the docker group. See installation instructions above for more about this.

## Installing

pip is the default package manager for Python, however, Ubuntu 23.04+ won't allow you to install CLI tools globally and you'll need to use a venv or another package management tool. Therefore, we recommend uv. A modern, faster package manager which allows global CLI tooling and comes with extra features such as easy upgrades.

### pip

```shell
pip install git+https://github.com/rdkcentral/sc.git@main
```

### uv

Install uv guide [here!](https://docs.astral.sh/uv/getting-started/installation/)

```shell
# Install sc as a global tool
uv tool install git+https://github.com/rdkcentral/sc.git@main

sc --help

# Update sc to latest
uv tool upgrade sc

# Uninstall sc
uv tool uninstall sc
```

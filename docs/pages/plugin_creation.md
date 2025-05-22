# Plugin Creation

## Contents

## Overview

To create an SC plugin we should create a Python package using setuptools with the prefix `sc-`. This must have a cli.py with a Click cli.

## cli.py

First we must install Click:

`python -m pip install click`

This file will contain the commands your plugin will contain. Below is an example:

```python
import click

# This is your overarching group. It MUST be called cli()
# The groups and commands below this group are added to sc directly
# putting any functionality in this function will do nothing and be skipped.
@click.group()
def cli():
    pass

# This will add a command namely command1 to sc 
# e.g you can run `sc command1` to run this group.
@cli.group()
def command1():
    """"""

@command1.command()
def subcommand1():
    """Your plugins functionality on running sc command1 subcommand1"""
    do_something()

@command1.command()
@click.argument('argument1')
def subcommand2(argument1):
    """Plugin functionality on running sc command1 subcommand2 [argument1]"""
```

There is much more to Click but above is the bare minimum for setting up a cli for your plugin. Read Click's docs [here](https://click.palletsprojects.com/en/stable/#).

## Making Your Plugin a Package

Now you have the basic functionality of your plugin the easiest way to make it into a package is with setuptools. To do this we create a setup.py file.

Start by installing setuptools and wheel:

```
python -m pip install setuptools
python -m pip install wheel
```

Make sure you have the correct file structure:

```
.
├── sc_my_plugin
│   ├── cli.py
│   └── __init__.py
└── setup.py
```

Your `__init__.py` file must contain:

`from .cli import cli`

Below is a basic example of your setup.py:

```python
from setuptools import setup

setup(
    name='sc-my-plugin', # This name MUST start with sc-
    version='1.0.0',
    packages=['sc-my-plugin'],
    install_requires=[
        'Click',
    ]
)
```

Then in the directory with your setup.py run command:

`python3 setup.py bdist_wheel`

This will create a `dist` folder with a .whl file inside. You can then pip install this with:

`python -m pip install dist/your_wheel_file.whl`

Now if you have `sc` installed as well you should be able to run:

`sc`

and get response:
```
Usage: sc [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  my-plugin   My plugin help message!
  version  Display SC Version
```

WARNING: ABOVE IS THE MOST BASIC INSTRUCTIONS FOR SETTING UP A PACKAGE FOR BETTER INSTRUCTIONS CHECK OUT THE SETUPTOOLS DOCS [HERE!](https://setuptools.pypa.io/en/latest/userguide/quickstart.html)

Congrats, you have created an SC plugin!


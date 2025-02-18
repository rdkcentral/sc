<div align="center">

# Software Control (SC) 
![language](https://img.shields.io/badge/language-python-239120)
![OS](https://img.shields.io/badge/OS-linux%2C%20macOS-0078D4)

SC is an CLI entry point that loads SC python plugin packages.

</div>

## Table of Contents
- [Installing](#installing)
- [Official Plugins](#official-plugins)
- [Create Your Own Plugin](#create-your-own-plugin)
  
## Installing

```shell
pip install git+https://github.com/rdkcentral/sc.git@master

# Look below for our official plugins
pip install git+https://github.com/rdkcentral/sc-docker.git@master

# Upon installing the above plugin we can use its commands
sc docker [options]
```

SC officially supports Python 3.10+.

## Official Plugins
### sc-docker
Run docker containers in a standardised manner. For more information click [here](https://github.com/rdkcentral/sc-docker).
```shell
python -m pip install sc-docker
```

## Create Your Own Plugin
[Create Your Own Plugin](docs/pages/plugin_creation.md)
# SC Docker Guide

SC docker module allows users to run docker containers in a standardised manner, using known docker registries.

## Table of Contents
  - [Quick Start](#quick-start)
  - [Usage](#usage)
  - [Design Doc](#design-doc)

## Quick Start

To work with private Docker registries, such as those used within our projects, you need to securely log in and store your credentials. Here's how:

* `sc docker login`
    * VIEW THE [LOGIN GUIDE!](login.md)
    * Enter your registry e.g. ghcr.io/organisation
    * Enter your registry type e.g. github
    * Are your credentials in your netrc? e.g n
    * Enter username
    * Enter API key
* Use `sc docker list` to find available dockers
* `sc docker run` docker_name command

## Usage

The usage document provides examples demonstrating the functionality of the module, which you can reference here: [Usage Manual](usage.md)

## Admin Tools

The administrator configuration index links to the Docker tool configuration:

```yaml
# /etc/sc/config.yaml
config_version: 2
docker: /etc/sc/tools/docker.yaml
```

Define the registry whitelist and server-wide credentials in the linked file:

```yaml
# /etc/sc/tools/docker.yaml
options:
  max_cpus: 4

whitelist:
  - ghcr.io/your-org

registries:
  ghcr.io/your-org:
    reg_type: github
    credential_store: config
    username: your_username
    api_key: your_api_key
```

An empty or omitted whitelist allows any registry. Administrator registry
definitions take precedence over user definitions with the same URL.
The `max_cpus` option limits how many CPUs a container can use and defaults to
4 when it is omitted.

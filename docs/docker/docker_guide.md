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

* To whitelist registries write them in the directory /etc/sc/docker_registry_whitelist seperated by newlines.
* To set server-wide registry logins add them to /etc/sc/.config.yaml in the following format:
```yaml
docker:
  ghcr.io/your-org:
    reg_type: github
    credential_store: config
    username: your_username
    api_key: your_api_key
```

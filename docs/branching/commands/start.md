# Branching Start Command

## Overview

Used to start new sc branching branches.

## Usage

`sc feature start <branch_name>`

Starts a feature branch from the develop branch on all repositories and the manifest.

`sc release start <tag_name>`

Starts a new release branch from the develop branch on all repositories and the manifest. When you sc finish this release will tag all repos with the tag name provided here.

`sc support start <branch_name> <base_tag>`

Starts a new support branch from a tag on all repositories and the manifest. Used for supporting changes to older tagged versions.

`sc hotfix start <branch_name> <base>`

Starts a new hotfix branch from a base (N.B. the base must be a support branch). Used for creating fixes to older supported versions.

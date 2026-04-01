# Branching Start Command

Used to start new sc branching branches.

## Usage

`sc feature start <branch_name>`

Starts a feature branch from the develop branch.

`sc release start <tag_name>`

Starts a new release branch from the develop branch. When you sc finish this release will tag all repos with the tag name provided here.

`sc support start <branch_name> <base_tag>`

Starts a new support branch from a tag. Used for supporting changes to older tagged versions.

`sc hotfix start <branch_name> <base>`

Starts a new hotfix branch from a base (N.B. the base must be a support branch). Used for creating fixes to older supported versions.

## Behaviour

- Git: Starts the branch in the git repository.
- Repo: Starts the branch in all projects and the manifest. Doesn't allow you to start branches that already exist on the manifest and pushes the branch to remote on the manifest to prevent starting the same branch twice.

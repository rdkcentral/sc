# Branching Reset Command

Used to reset git repositories.

## Usage

`sc reset`

## Behaviour

- Git: Not implemented; prints an error instructing use of `git reset` instead.
- Repo: Runs `git reset --hard <manifest_revision>` in all projects without a `GIT_LOCK_STATUS`, resetting the project to the revision in the manifest.

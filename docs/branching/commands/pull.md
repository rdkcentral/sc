# Branching Pull Command

Used to pull from remote.

## Usage

`sc <branch_type> pull <optional_branch_name>`

## Behaviour

- Git: Runs `git pull <remote> <branch_name>` in the git repository.
- Repo: Checks out the manifest at the branch supplied, pulls it, downloads the projects at the specified revisions in the manifest and either checks the project out to that revision if the branch doesn't exist locally or merges it with the local branch to bring it to the latest state from the manifest.
# Branching Push Command

Used to push the local state to the remote.

## Usage

`sc <branch_type> push <optional_branch_name>`

## Behaviour

- Git: Runs `git push <remote> <branch>`.
- Repo: Runs `git push <remote> <branch>` on all projects, updates the revisions in the manifest and then runs `git push origin <branch>` in the manifest.
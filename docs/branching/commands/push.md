# Branching Push Command

Used to push the local state to the remote.

## Usage

`sc <branch_type> push <optional_branch_name>`

## Behaviour

- Git: Runs `git push -u <remote> <branch>` and then pushes all local tags with `git push --tags`.
- Repo: Pushes each eligible project branch and its tags; `READ_ONLY` projects are skipped and `TAG_ONLY` projects push tags only. It updates and commits manifest revisions, then pushes the manifest branch and tags.

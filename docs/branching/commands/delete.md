# Branching Delete Command

Delete a branch.

## Usage

`sc <feature/release/hotfix> delete <branch_name>`

## Flags

`-r, --remote` - Delete the branch on the remote as well.

## Behaviour

Git: Delete the branch in the current git repository.
Repo: Delete the branch in all projects without a `GIT_LOCK_STATUS` annotation and in the manifest repository.

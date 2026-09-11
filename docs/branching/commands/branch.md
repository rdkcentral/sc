# Branching Branch Commands

## `sc branch rename <old_branch> <new_branch>`

### Behaviour

Git: Rename the current git branch.
Repo: Rename the branch of all projects without a `GIT_LOCK_STATUS` in the manifest and the manifests branch.

## `sc branch show` or `sc show branch`

### Behaviour

- Git: Shows branch information for your git repository.
- Repo: Shows branch information, lock status and groups of all projects.

## `sc branch rm_merged`

### Behaviour

Git: Remove all feature branches that have been merged into develop both locally and on the remote.
Repo: Remove all feature branches that have been merged into develop in the manifest repository. Deletes the branches on all projects and the manifest repository.

### Flags

`-n, --no-merged` - Show feature branches that haven't been merged into develop instead.
`-a, --all` - Show all feature branches instead.
`-y, --yes` - Delete branches without being prompted.
`-g, --git` - Target the git repository you are currently in instead of looking for a Repo workspace to target.
`-d, --dry` - Dry run, display which branches would be targeted if you ran this command.

# Branching Finish Command

Used to finish a feature, release, or hotfix branch.

## Usage

`sc feature finish <branch_name>`
`sc release finish <branch_name>`
`sc hotfix finish <branch_name> <base_branch>`

## Behaviour

- Git: Runs `git-flow <branch_type> finish` in the git repository.
- Repo: Finishes the branch in each project without a lock annotation; `READ_ONLY` projects are skipped and `TAG_ONLY` projects are tagged without being finished for release/hotfix. It then finishes the manifest and commits updated revisions on the target branch.

### How branches are finished:
- feature: Merges the feature branch into develop.
- release: Merges the release branch into master, tags the master branch, and then merges the master branch into develop.
- hotfix: Merges the hotfix branch into the support branch it was created from.

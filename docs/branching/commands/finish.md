# Branching Finish Command

Used to finish a feature, release, or hotfix branch.

## Usage

`sc <feature/release/hotfix> finish <optional_branch_name>`

## Behaviour

- Git: Runs `git-flow <branch_type> finish` in the git repository.
- Repo: Runs `git-flow <branch_type> finish` in all projects. After all projects are merged runs `git-flow <branch_type> finish` in the manifest and then creates another commit on the manifest target branch with updated manifest revisions.

### How branches are finished:
- feature: Merges the feature branch into develop.
- release: Merges the release branch into master, tags the master branch, and then merges the master branch into develop.
- hotfix: Merges the hotfix branch into the support branch it was created from.
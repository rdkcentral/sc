# Branching Init Command

Run inside a git repository or git-repo workspace to set it up to work with sc.

## Usage

`sc init`

## Behaviour

- Git: Runs `git-flow init` in the git repository.
- Repo: Runs git-flow initialization in the manifest and each project without a `GIT_LOCK_STATUS` annotation. Projects with `READ_ONLY` or `TAG_ONLY` are skipped; alternate master or develop branches must be specified with manifest annotations. See the [manifest documentation](../manifest.md) for more.

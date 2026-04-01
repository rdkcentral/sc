# Brnaching Init Command

Run inside a git repository or git-repo workspace to set it up to work with sc.

## Usage

`sc init`

## Behaviour

- Git: Runs `git-flow init` in the git repository.
- Repo: Runs git flow init in all projects and the manifest. If any of your projects in your git-repo workspace have an alternative master or develop branch, they should have an annotation in the manifest specifying that. Check out the [manifest documentation](../manifest.md) for more.

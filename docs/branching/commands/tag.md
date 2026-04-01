# Branching Tag Commands

## `sc tag show <tag>` or `sc show tag <tag>`

### Behaviour

- Git: Shows information about the particular tag in the git repository.
- Repo: Shows information about the particular tag in all projects.

## `sc tag list`

### Behaviour

- Git: Lists all tags in the git repository.
- Repo: Lists all tags in the manifest.

## `sc tag create <tag>`

### Behaviour

- Git: Runs `git tag <tag>` in the git repository.
- Repo: Runs `git tag <tag>` in all non READ_ONLY projects and the manifest.

## `sc tag rm <tag>`

### Behaviour

- Git: Deletes the tag from the git repository.
- Repo: Deletes the tag from all projects and the manifest.

### Flags

- `-r`, `--remote`: Removes the tag from the remote as well.

## `sc tag push <tag>`

### Behaviour

- Git: Pushes the tag in the git repository.
- Repo: Pushes the tag in all non READ_ONLY projects and the manifest.

## `sc tag check <tag>`

### Behaviour

- Git: Checks if the tag exists in the git repository.
- Repo: Checks if the tag exists in all projects and the manifest.
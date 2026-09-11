# Branching Group Commands

Groups are only applicable to Repo workspaces and not git projects. In the manifest projects can be assigned a group:

```xml
  <project name="remote/project/path.git" revision="12345" groups="GroupA">
```

Then group commands can be used to act on all projects in a certain group.

## `sc show group` or `sc show group <group>`

List all groups in a manifest or show information about projects in a particular group.

## `sc group tag <group> <tag>`

Apply a git tag to all projects that belong to a group.

### Options

`-m, --message` - Apply a message to the tags.
`-p, --push` - Push the tags to remote.

## `sc group checkout <group> <branch>`

Checkout a branch for all projects belonging to a group.

## `sc group cmd <group> <command>`

Run a command in all projects belonging to a group.

## `sc group pull <group>`

Run git pull in all projects belonging to a group.

## `sc group fetch <group>`

Run git fetch in all projects belonging to a group.

## `sc group push <group>`

Run git push in all projects belonging to a group.

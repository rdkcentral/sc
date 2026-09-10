# sc branching

## Introduction

sc branching is a collection of tools used for managing git repositories or repo workspaces. It allows for git-flow branching strategy operations on many repositories at once along with other useful tools.

## git-repo (Repo)

sc branching works closely with Googles [git-repo](https://gerrit.googlesource.com/git-repo) and uses it to allow users to apply git-flow branching strategy on multiple repositories at once.

Useful terms and ideas when discussing Repo in these docs:

- Project: A git repository cloned and managed by Repo.
- [Manifest](manifest.md): An xml file describing the projects to be cloned and managed by Repo.
- Repo workspace: The collective of projects and a manifest owned by Repo.

## Overview of completing a feature.

### Creating a branch.

After downloading a repo project, usually using [sc clone](../clone/clone_guide.md) then proceed to start a feature branch:

`sc feature start <prefix><ticket_number>_<synopsis>`

Using the above branch format will allow you to use `sc review` to create a pull request and update the ticket associated with the feature.

### Making changes.

Make changes in either the git repository or Repo projects inside your workspace, making sure to `git commit` the changes in all Repo projects.

Once you've committed the changes use:

`sc feature push <branch_name>`

To push your feature branch to the remote.

### Finishing your feature branch.

Once you are happy with your changes use `sc review` to get urls to create pull requests for updated repositories/projects. After the reviews are completed use:

`sc feature finish <branch_name>`

To merge your changes into develop, you may have to fix some merge conflicts and rerun this command.

Once that is complete use:

`sc develop push`

To push the updated develop branch to the remote.

## Adding a new project to the manifest

To add a new project you must update the manifest inside your feature branch. The manifest is located from the top directory in `.repo/manifests`.

Once added you can use `sc feature push` to update the manifest in your feature branch and bring the update to the develop branch with `sc feature finish`.

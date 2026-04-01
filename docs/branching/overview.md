# sc branching

## Introduction

sc branching is a collection of tools used for managing git repositories or repo workspaces. It allows for git-flow branching strategy operations on many repositories at once along with other useful tools.

## git-repo (Repo)

sc branching works closely with Googles [git-repo](https://gerrit.googlesource.com/git-repo) and uses it to allow users to apply git-flow branching strategy on multiple repositories at once.

Useful terms and ideas when discussing Repo in these docs:

- Project: A git repository cloned and managed by Repo.
- Manifest: An xml file describing the projects to be cloned and managed by Repo.
- Repo workspace: The collective of projects and a manifest owned by Repo.

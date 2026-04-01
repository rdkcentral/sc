# Manifest

The manifests we use are superset of a [Repo manifest](https://gerrit.googlesource.com/git-repo/+/HEAD/docs/manifest-format.md) excluding not supporting `<submanifest>` elements currently.

The manifest defines the canonical state of your Repo workspace when using sc. All project revisions are derived from it.

When referring to actions "on a branch", this means the set of project revisions defined by the manifest at that branch not the local Git branches of individual repositories.

## Annotations

We allow the use of project annotations to set up extra configuration on projects.

An example of a manifest with an annotated project:

```xml
<manifest>
  <remote name="remote_name" fetch="remote_uri"/>
  <default remote="sky_external"/>
  <project name="remote/project/path.git" revision="291bd9d660c385c9ddae293028fcaf1941d2d431">
    <annotation name="ANNOTATION_NAME" value="ANNOTATION_VALUE"/>
  </project>
</manifest>
```

### Supported Annotations

- GIT_FLOW_BRANCH_MASTER: An alternative master branch to use with git-flow branching operations.
- GIT_FLOW_BRANCH_DEVELOP: An alternative develop branch to use with git-flow-branching operations.
- GIT_LOCK_STATUS: Has 2 options for values
  - READ_ONLY: Will never be pushed to remote or tagged. If you switch the revision and do a push or finish the manifest will be updated with the new revision.
  - TAG_ONLY: Will never be pushed but will be tagged. If you switch the revison and do a push or finish the manifest will be updated with the new revision.
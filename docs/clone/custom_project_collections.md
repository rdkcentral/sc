# Adding Your Own Custom Projects and Collections to sc-clone

To add your own custom projects to sc-clone there are a few steps. Firstly we need to 
create a "Project Collection" configuration, this needs to then be hosted online
and finally we can add this to sc clone using `sc add-project-list`.

## Creating a "Project Collection"

A project collection is a yaml file that describes various projects. These projects can either be git projects or repo projects.

### Example Project Collection
```yaml
category:
  subcategory:
    project1:
      type: repo
      project_repo: 'git@github.com/your/manifest.git'
      manifest_xml: 'your_manifest.xml'
      branch: develop
    project2:
      type: git
      project_repo: git@github.com/your/repo.git
      branch: develop
      description: Description must be included in a project!
```

You can have as many indented levels of categories or subcategories as you like.

## Project Fields

### Required Fields

* type: The type of project. Supported options are shown below:
  * git
  * repo
* project_repo: The repository URL.
  * *For `repo` projects this is the manifest URL.*

### Optional Fields

* description: Description of the project.
  * This will be displayed with the project, when projects are listed.
* branch: The branch to clone.
  * If not set, the default branch for the repository will be used.

### repo Specific Optional Fields

* manifest: The manifest file to use.
  * Defaults to `default.xml`
* repo_url: The url of the git-repo project to use.
  * Defaults to googles latest version.
* repo_rev: The revision of the git-repo project to use.
  * Defaults to the latest version on whichever URL you chose above.

## Adding this to SC Clone

Firstly, this must be hosted online. Then you must get the link to the raw file for downloading. 

Then use `sc add-project-list`.

This will prompt you for a name, you can use anything that will help you know which collection of projects this is.

Then it will prompt you for a URL, this is the raw url from before.

Next, it will ask if the file is private or not, select private if a token or password is required to download the file.

If it is private it will ask where the file is hosted and you can choose from a list of supported platforms. If you don't see the platform you wish to use for hosting raise an issue on sc-clones github page. Then it will ask you for an API token for your chosen platform. The method for getting this API token depends on the platform selected.

If all is correct, your project collection is now added to SC!

## Advanced Usage

### Project Defaults

You can have a project_defaults section to store default information about projects.

For example:

```yaml
project_defaults:
  default: &default
    type: repo
    branch: develop
category:
  subcategory:
    project1:
      <<: *default
      project_repo: 'git@github.com/your/manifest.git'
      manifest: 'your_manifest.xml'
```

from pathlib import Path

import click
from git import Repo
from pydantic import BaseModel

from .cloner import Cloner

class GitClonerConfig(BaseModel):
    uri: str
    branch: str | None = None
    no_tags: bool = False


class GitCloner(Cloner):
    """Clones a git repository.
    
    Args:
        uri (str): The repository URL to clone.
        directory (str, optional): The directory where the repository should be cloned. 
            Defaults to None.
        branch (str, optional): The branch to clone. If None, the default branch is used.
        no_tags (bool, optional): Clone without tags.
    """

    def __init__(
            self, 
            config: GitClonerConfig
        ):
        self.config = config

    def clone(self, directory: Path):
        cmd = ["git", "clone"]

        if self.config.no_tags:
            cmd.append("--no-tags")

        if self.config.branch:
            cmd.extend(["--branch", self.config.branch])

        cmd.append(self.config.uri)
        cmd.append(str(directory))

        click.secho(" ".join(cmd), fg="green")

        Repo.clone_from(
            self.config.uri, 
            directory, 
            branch=self.config.branch, 
            multi_options=["--no-tags"] if self.config.no_tags else None
        )
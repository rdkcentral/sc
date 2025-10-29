from pathlib import Path

from git_flow_library import GitFlowLibrary
from .git_cloner import GitCloner, GitClonerConfig

class GitFlowCloner(GitCloner):
    """Clone a git project and initialise it for git-flow."""
    def __init__(self, config: GitClonerConfig):
        super().__init__(config)

    def clone(self, directory: Path):
        """Clones the Git repository and initializes GitFlow in the cloned directory."""
        super().clone(directory)
        GitFlowLibrary.init(directory)
from abc import ABC, abstractmethod
from enum import Enum
import logging
from pathlib import Path
import subprocess
import sys

logger = logging.getLogger(__name__)

class RefType(Enum):
    BRANCH = "BRANCH"
    TAG = "TAG"
    SHA = "SHA"

class Cloner(ABC):
    @abstractmethod
    def clone(self, directory: Path):
        pass

    def _is_branch_tag_or_sha(self, repo_uri: str, ref: str):
        refs = subprocess.run(
            ["git", "ls-remote", repo_uri], capture_output=True, text=True).stdout
        
        if f"refs/heads/{ref}" in refs:
            return RefType.BRANCH
        elif f"refs/tags/{ref}" in refs:
            return RefType.TAG
        else:
            return RefType.SHA

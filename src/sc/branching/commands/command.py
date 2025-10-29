from dataclasses import dataclass
import logging
from pathlib import Path
import sys

from git_flow_library import GitFlowLibrary
from sc.branching.exceptions import ScInitError

logger = logging.getLogger(__name__)

@dataclass
class Command:
    top_dir: Path

    def run_repo_command(self):
        logger.error("Repo command not implemented!")
        sys.exit(1)
        
    def run_git_command(self):
        logger.error("Git command not implemented!")
        sys.exit(1)

    def _is_sc_initialised(self) -> bool:
        return GitFlowLibrary.is_gitflow_enabled(self.top_dir / '.repo' / 'manifests')

    def _error_on_sc_uninitialised(self):
        if not self._is_sc_initialised():
            raise ScInitError("SC is not initialised! Run `sc init`")

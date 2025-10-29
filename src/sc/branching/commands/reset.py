from pathlib import Path
import subprocess
import logging
from .command import Command
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

class Reset(Command):
    def _reset_repo(self,dir,revision):
        subprocess.run(
            ["git","reset","--hard",revision],
            cwd = dir,
            encoding = "utf-8",
            check = False,
        )

    def run_git_command(self):
        logger.error("Not implemented for Git use Git reset instead")
    
    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        for project in manifest.projects:
            if project.lock_status is not None:
                continue
            
            self._reset_repo(self.top_dir/project.path,project.revision)
